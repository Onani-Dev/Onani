# -*- coding: utf-8 -*-
import datetime
import os
import re
import shutil
import sqlite3
import subprocess
import time

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import make_url

from onani import db


class MaintenanceError(RuntimeError):
    """Raised when an admin maintenance operation cannot be completed."""


_UNSUPPORTED_POSTGRES_RESTORE_SETTINGS = {
    "transaction_timeout",
}

_POSTGRES_RESTORE_DROP_PREFIXES = (
    "ALTER TABLE ONLY ",
    "ALTER TABLE ",
    "DROP TABLE ",
    "DROP SEQUENCE ",
    "DROP INDEX ",
    "DROP VIEW ",
    "DROP MATERIALIZED VIEW ",
    "DROP FUNCTION ",
    "DROP TYPE ",
    "DROP EXTENSION ",
    "DROP SCHEMA ",
)

_POSTGRES_RESTORE_DEADLOCK_RETRIES = 3


def optimize_database() -> str:
    """Run the database engine's cheapest built-in maintenance command."""
    engine = db.engine
    dialect = engine.url.get_backend_name()

    if dialect == "sqlite":
        raw = engine.raw_connection()
        try:
            raw.isolation_level = None
            cursor = raw.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.close()
        finally:
            raw.close()
        return "SQLite VACUUM and ANALYZE completed."

    if dialect == "postgresql":
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("VACUUM ANALYZE"))
        return "PostgreSQL VACUUM ANALYZE completed."

    raise MaintenanceError(f"Database maintenance is not implemented for '{dialect}'.")


def clear_thumbnail_cache(images_dir: str, avatars_dir: str) -> dict:
    """Delete generated thumbnail caches under the image and avatar roots."""
    deleted_dirs = 0
    deleted_files = 0

    for root in (images_dir, avatars_dir):
        thumbs_dir = os.path.join(root, ".thumbs")
        if not os.path.isdir(thumbs_dir):
            continue
        for _, dirnames, filenames in os.walk(thumbs_dir):
            deleted_files += len(filenames)
            deleted_dirs += len(dirnames)
        shutil.rmtree(thumbs_dir)
        deleted_dirs += 1

    return {
        "deleted_dirs": deleted_dirs,
        "deleted_files": deleted_files,
    }


def scan_post_storage(images_dir: str) -> dict:
    """Scan stored post files and report missing originals / video thumbnails."""
    from onani.models import Post
    from onani.services.files import shard_path

    video_exts = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
    scanned = 0
    missing_originals = 0
    missing_video_thumbnails = 0

    for post in Post.query.order_by(Post.id.asc()).all():
        scanned += 1
        source_path = shard_path(images_dir, post.filename)
        if not os.path.isfile(source_path):
            missing_originals += 1
            continue

        if (post.file_type or "").lower() in video_exts:
            thumb_name = f"{post.filename.rsplit('.', 1)[0]}.jpg"
            thumb_path = shard_path(images_dir, thumb_name)
            if not os.path.isfile(thumb_path):
                missing_video_thumbnails += 1

    return {
        "scanned": scanned,
        "missing_originals": missing_originals,
        "missing_video_thumbnails": missing_video_thumbnails,
    }


def create_database_backup() -> tuple[bytes, str, str]:
    """Return a database backup as bytes, plus filename and mimetype."""
    engine = db.engine
    dialect = engine.url.get_backend_name()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if dialect == "sqlite":
        raw = engine.raw_connection()
        try:
            script = "\n".join(raw.connection.iterdump()) + "\n"
        finally:
            raw.close()
        filename = f"onani-backup-{timestamp}.sql"
        return script.encode("utf-8"), filename, "application/sql"

    if dialect == "postgresql":
        cmd, env = _postgres_cli_base("pg_dump")
        cmd.extend([
            "--no-owner",
            "--no-privileges",
            "--format=plain",
            "--encoding=UTF8",
            db.engine.url.database,
        ])
        proc = subprocess.run(cmd, env=env, capture_output=True, check=False)
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace").strip()
            raise MaintenanceError(stderr or "pg_dump failed.")
        filename = f"onani-backup-{timestamp}.sql"
        return proc.stdout, filename, "application/sql"

    raise MaintenanceError(f"Backups are not implemented for '{dialect}'.")


def restore_database_backup(backup_bytes: bytes) -> str:
    """Restore the configured database from a plain SQL backup."""
    engine = db.engine
    dialect = engine.url.get_backend_name()
    db.session.remove()

    if dialect == "sqlite":
        script = backup_bytes.decode("utf-8")
        db.drop_all()
        raw = engine.raw_connection()
        try:
            raw.isolation_level = None
            cursor = raw.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.executescript(script)
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
        except sqlite3.Error as exc:
            raise MaintenanceError(str(exc)) from exc
        finally:
            raw.close()
        return "SQLite database restored from backup."

    if dialect == "postgresql":
        restore_bytes = _sanitize_postgres_restore_sql(backup_bytes)
        return _restore_postgres_backup(restore_bytes)

    raise MaintenanceError(f"Restore is not implemented for '{dialect}'.")


def _postgres_cli_base(program: str) -> tuple[list[str], dict]:
    url = make_url(str(db.engine.url))
    if not url.host or not url.database or not url.username:
        raise MaintenanceError("PostgreSQL backups require host, database, and username in DATABASE_URL.")

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    cmd = [
        program,
        "--host",
        url.host,
        "--port",
        str(url.port or 5432),
        "--username",
        url.username,
    ]
    return cmd, env


def _sanitize_postgres_restore_sql(backup_bytes: bytes) -> bytes:
    """Drop directives that break restores across PostgreSQL versions and states."""
    script = backup_bytes.decode("utf-8", errors="replace")
    setting_pattern = re.compile(r"^\s*SET\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=", re.IGNORECASE)
    cleanup_pattern = re.compile(
        r"^\s*(ALTER\s+TABLE(?:\s+ONLY)?\s+.+\s+DROP\s+CONSTRAINT|"
        r"DROP\s+(?:TABLE|SEQUENCE|INDEX|VIEW|MATERIALIZED\s+VIEW|FUNCTION|TYPE|EXTENSION|SCHEMA))\b",
        re.IGNORECASE,
    )

    filtered_lines = []
    for line in script.splitlines(keepends=True):
        match = setting_pattern.match(line)
        if match and match.group(1).lower() in _UNSUPPORTED_POSTGRES_RESTORE_SETTINGS:
            continue
        if cleanup_pattern.match(line):
            continue
        filtered_lines.append(line)

    return "".join(filtered_lines).encode("utf-8")


def _restore_postgres_backup(restore_bytes: bytes) -> str:
    db_name = db.engine.url.database
    cmd, env = _postgres_cli_base("psql")
    cmd.extend([
        "-v",
        "ON_ERROR_STOP=1",
        "-d",
        db_name,
    ])

    last_error = ""
    for attempt in range(1, _POSTGRES_RESTORE_DEADLOCK_RETRIES + 1):
        _try_terminate_postgres_connections(db_name)
        _reset_postgres_public_schema()
        proc = subprocess.run(cmd, env=env, input=restore_bytes, capture_output=True, check=False)
        if proc.returncode == 0:
            _stamp_alembic_to_local_heads()
            return "PostgreSQL database restored from backup."

        stderr = proc.stderr.decode("utf-8", errors="replace").strip()
        last_error = stderr or "psql restore failed."
        if "deadlock detected" not in last_error.lower() or attempt >= _POSTGRES_RESTORE_DEADLOCK_RETRIES:
            break

        time.sleep(0.5 * attempt)

    raise MaintenanceError(last_error)


def _try_terminate_postgres_connections(db_name: str) -> None:
    """Best-effort kill of competing sessions to reduce restore lock contention."""
    try:
        with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :db_name
                  AND pid <> pg_backend_pid()
                """
            ), {"db_name": db_name})
    except Exception:
        # Not all deployments grant permission to terminate backends.
        pass


def _reset_postgres_public_schema() -> None:
    """Recreate the public schema so restore runs against an empty target."""
    with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))


def _stamp_alembic_to_local_heads() -> None:
    """Force alembic_version in the restored DB to this codebase's known heads."""
    heads = _discover_local_alembic_heads()
    if not heads:
        return

    with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL
            )
            """
        ))
        conn.execute(text("DELETE FROM alembic_version"))
        for head in heads:
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES (:version_num)"), {
                "version_num": head,
            })


def _discover_local_alembic_heads() -> list[str]:
    candidates = [
        os.path.join(os.getcwd(), "migrations", "alembic.ini"),
        "/onani/migrations/alembic.ini",
    ]
    alembic_ini = next((path for path in candidates if os.path.isfile(path)), None)
    if not alembic_ini:
        return []

    cfg = AlembicConfig(alembic_ini)
    script = ScriptDirectory.from_config(cfg)
    return [head for head in script.get_heads() if head]