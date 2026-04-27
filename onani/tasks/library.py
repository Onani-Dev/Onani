# -*- coding: utf-8 -*-
"""Celery task for scanning an ExternalLibrary directory.

The task walks the configured path, discovers supported media files, and
imports any new ones as posts.  Progress is stored on the ExternalLibrary row
(``last_scan_status``, ``last_scan_at``) so the front-end can poll.
"""

import datetime
import hashlib
import os
from urllib.parse import quote

from celery import shared_task

from . import db

# Supported extensions (lower-case without leading dot).
_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "avif", "bmp", "tiff", "tif"}
_VIDEO_EXTS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
SUPPORTED_EXTS = _IMAGE_EXTS | _VIDEO_EXTS


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_scan_directory(root: str, recursive: bool = True):
    """Yield absolute paths for supported media files under *root* as discovered."""
    if recursive:
        for dirpath, _dirnames, filenames in os.walk(root):
            for fname in filenames:
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                if ext in SUPPORTED_EXTS:
                    yield os.path.join(dirpath, fname)
        return

    for entry in os.scandir(root):
        if not entry.is_file():
            continue
        ext = entry.name.rsplit(".", 1)[-1].lower() if "." in entry.name else ""
        if ext in SUPPORTED_EXTS:
            yield entry.path


def _external_url(library_id: int, library_root: str, file_path: str) -> str:
    rel_path = os.path.relpath(file_path, library_root)
    rel_path = rel_path.replace(os.sep, "/")
    safe_rel = "/".join(quote(part, safe="") for part in rel_path.split("/") if part and part != ".")
    safe_library = quote(str(library_id), safe="")
    return f"/external/{safe_library}/{safe_rel}"


@shared_task(
    bind=True,
    soft_time_limit=21600,  # 6 h soft limit for very large libraries
    time_limit=21900,
)
def scan_library(self, library_id: int):
    """Walk an ExternalLibrary's directory and import any new media files.

    Progress is reported via ``self.update_state`` so the API endpoint can
    expose it to the client; the library row is also updated in-place.
    """
    from celery.exceptions import SoftTimeLimitExceeded
    from flask import current_app
    from onani.models import ExternalLibrary, ExternalLibraryFile, Post
    from onani.models.post import PostRating
    from onani.services.posts import create_post
    from onani.services.files import get_file_data, get_video_data, detect_video_format

    db.session.remove()

    def _update(state: str, meta: dict):
        try:
            self.update_state(state=state, meta=meta)
        except Exception:
            pass

    library = ExternalLibrary.query.get(library_id)
    if library is None:
        return {"error": f"Library {library_id} not found."}

    if not os.path.isdir(library.path):
        library.last_scan_status = "FAILED"
        library.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return {"error": f"Path does not exist or is not a directory: {library.path}"}

    logs = [f"Starting scan of '{library.name}' ({library.path})"]
    library.last_scan_status = "SCANNING"
    library.last_scan_task_id = self.request.id
    db.session.commit()

    _update("PROGRESS", {"library_id": library_id, "logs": logs})

    # -----------------------------------------------------------------------
    # Phase 1: stream discovery + import
    # -----------------------------------------------------------------------
    now = datetime.datetime.now(datetime.timezone.utc)
    existing: dict[str, ExternalLibraryFile] = {
        f.file_path: f
        for f in library.files.all()
    }

    discovered_count = 0
    processed_count = 0
    seen_paths: set[str] = set()
    new_count = 0
    retry_count = 0
    imported_count = 0
    failed_count = 0
    skipped_count = 0

    # Resolve the importer User for post ownership (the library owner).
    from onani.models import User
    owner = User.query.get(library.owner_id) if library.owner_id else None

    # Parse default tags once.
    default_tags: set = set(
        t.strip() for t in (library.default_tags or "").split() if t.strip()
    )

    # Validate default rating.
    valid_ratings = {r.value for r in PostRating}
    default_rating = library.default_rating if library.default_rating in valid_ratings else "q"

    # Commit in batches to avoid per-file expire/reload cycles.
    _BATCH_SIZE = 100
    _batch_dirty = 0

    def _flush_batch(force: bool = False):
        nonlocal _batch_dirty
        if force or _batch_dirty >= _BATCH_SIZE:
            db.session.commit()
            _batch_dirty = 0

    discovery_interval = 25
    import_log_interval = 25

    try:
        for path in _iter_scan_directory(
            library.path,
            recursive=bool(getattr(library, "recursive", True)),
        ):
            discovered_count += 1
            seen_paths.add(path)

            if discovered_count == 1 or discovered_count % discovery_interval == 0:
                logs.append(
                    f"Discovered {discovered_count} media file(s) so far. Latest: {os.path.basename(path)}"
                )
                _update("PROGRESS", {
                    "library_id": library_id,
                    "current": processed_count,
                    "total": discovered_count,
                    "discovered": discovered_count,
                    "imported": imported_count,
                    "failed": failed_count,
                    "skipped": skipped_count,
                    "logs": logs,
                })

            file_rec = existing.get(path)
            if file_rec is None:
                file_rec = ExternalLibraryFile(
                    library_id=library_id,
                    file_path=path,
                    first_seen_at=now,
                    last_seen_at=now,
                    status="PENDING",
                )
                db.session.add(file_rec)
                db.session.flush()
                existing[path] = file_rec
                new_count += 1
            else:
                file_rec.last_seen_at = now
                if file_rec.status in ("FAILED", "MISSING"):
                    file_rec.status = "PENDING"
                    retry_count += 1

            if file_rec.status != "PENDING":
                continue

            processed_count += 1
            try:
                # Compute hash first to detect duplicates without a full import.
                sha = _sha256_file(path)

                # Check for a duplicate post by hash.
                existing_post = Post.query.filter_by(sha256_hash=sha).first()
                if existing_post:
                    file_rec.status = "IMPORTED"
                    file_rec.post_id = existing_post.id
                    file_rec.sha256_hash = sha
                    file_rec.imported_at = now
                    file_rec.error = None
                    _batch_dirty += 1
                    _flush_batch()
                    skipped_count += 1
                    if processed_count == 1 or processed_count % import_log_interval == 0:
                        logs.append(
                            f"[{processed_count}] Skipped (duplicate hash): {os.path.basename(path)}"
                        )
                    _update("PROGRESS", {
                        "library_id": library_id,
                        "current": processed_count,
                        "total": discovered_count,
                        "discovered": discovered_count,
                        "imported": imported_count,
                        "failed": failed_count,
                        "skipped": skipped_count,
                        "logs": logs,
                    })
                    continue

                with open(path, "rb") as fh:
                    file_data = fh.read()

                video_fmt = detect_video_format(file_data)
                if not video_fmt:
                    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
                    if ext in _VIDEO_EXTS:
                        video_fmt = ext

                original_filename = os.path.basename(path)

                if video_fmt:
                    image_file, filesize, hash_sha256, hash_md5, width, height, filename, file_type = (
                        get_video_data(file_data, input_format=video_fmt)
                    )
                else:
                    image_file, filesize, hash_sha256, hash_md5, width, height, filename, file_type = (
                        get_file_data(file_data)
                    )

                post = create_post(
                    source="External",
                    description="",
                    uploader=owner,
                    rating=default_rating,
                    image_file=image_file,
                    filesize=filesize,
                    hash_sha256=hash_sha256,
                    hash_md5=hash_md5,
                    width=width,
                    height=height,
                    filename=filename,
                    file_type=file_type,
                    original_filename=original_filename,
                    tags=default_tags,
                    images_dir=current_app.config["IMAGES_DIR"],
                    can_create_tags=True,
                    tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                    post_min_tags=current_app.config["POST_MIN_TAGS"],
                    imported_from=_external_url(library.id, library.path, path),
                    is_external=True,
                    persist_file=False,
                )

                file_rec.status = "IMPORTED"
                file_rec.post_id = post.id
                file_rec.sha256_hash = hash_sha256
                file_rec.imported_at = datetime.datetime.now(datetime.timezone.utc)
                file_rec.error = None
                _batch_dirty += 1
                # Always flush after a new post to keep post IDs stable before
                # referencing them in subsequent iterations.
                _flush_batch(force=True)

                imported_count += 1
                if processed_count == 1 or processed_count % import_log_interval == 0:
                    logs.append(
                        f"[{processed_count}] Imported: {os.path.basename(path)} -> post #{post.id}"
                    )

            except Exception as e:
                db.session.remove()
                _batch_dirty = 0
                file_rec_fresh = ExternalLibraryFile.query.filter_by(
                    library_id=library_id,
                    file_path=path,
                ).first()
                if file_rec_fresh:
                    file_rec_fresh.status = "FAILED"
                    file_rec_fresh.error = str(e)
                    db.session.commit()
                failed_count += 1
                if processed_count == 1 or processed_count % import_log_interval == 0:
                    logs.append(
                        f"[{processed_count}] Failed: {os.path.basename(path)}: {e}"
                    )

            _update("PROGRESS", {
                "library_id": library_id,
                "current": processed_count,
                "total": discovered_count,
                "discovered": discovered_count,
                "imported": imported_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "logs": logs,
            })

    except SoftTimeLimitExceeded:
        db.session.remove()
        lib_partial = ExternalLibrary.query.get(library_id)
        if lib_partial:
            lib_partial.last_scan_status = "PARTIAL" if (imported_count or skipped_count or failed_count) else "FAILED"
            lib_partial.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
        logs.append(
            "Scan reached time limit during discovery/import; rerun scan to continue."
        )
        return {
            "library_id": library_id,
            "error": "Scan timed out during discovery/import.",
            "imported": imported_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "logs": logs,
        }
    except Exception as e:
        db.session.remove()
        library_err = ExternalLibrary.query.get(library_id)
        if library_err:
            library_err.last_scan_status = "FAILED"
            library_err.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
        logs.append(f"Scan failed: {e}")
        return {
            "library_id": library_id,
            "error": f"Directory scan/import failed: {e}",
            "imported": imported_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "logs": logs,
        }

    # Mark files that have disappeared from disk as MISSING.
    missing_count = 0
    for path, rec in existing.items():
        if path not in seen_paths and rec.status not in ("MISSING", "IMPORTED"):
            rec.status = "MISSING"
            _batch_dirty += 1
            missing_count += 1

    _flush_batch(force=True)

    logs.append(
        f"Discovery complete. Found: {discovered_count}, new: {new_count}, "
        f"retrying failed: {retry_count}, missing: {missing_count}."
    )
    _update("PROGRESS", {
        "library_id": library_id,
        "current": processed_count,
        "total": max(discovered_count, processed_count),
        "discovered": discovered_count,
        "imported": imported_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "logs": logs,
    })

    # -----------------------------------------------------------------------
    # Phase 4: finalise
    # -----------------------------------------------------------------------
    library_fresh = ExternalLibrary.query.get(library_id)
    if library_fresh:
        library_fresh.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
        library_fresh.last_scan_status = "FAILED" if failed_count and not imported_count else "SUCCESS"
        library_fresh.last_scan_task_id = self.request.id
        db.session.commit()

    # Recount tag post_counts so the Tags page reflects new imports.
    if imported_count:
        try:
            from onani.models import Tag
            for tag in Tag.query.all():
                tag.recount_posts()
            db.session.commit()
        except Exception:
            pass

    summary = (
        f"Scan complete. Discovered: {discovered_count}, imported: {imported_count}, "
        f"failed: {failed_count}, skipped/duplicates: {skipped_count}."
    )
    logs.append(summary)

    return {
        "library_id": library_id,
        "imported": imported_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "logs": logs,
    }
