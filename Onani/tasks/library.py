# -*- coding: utf-8 -*-
"""Celery task for scanning an ExternalLibrary directory.

The task walks the configured path, discovers supported media files, and
imports any new ones as posts.  Progress is stored on the ExternalLibrary row
(``last_scan_status``, ``last_scan_at``) so the front-end can poll.
"""

import datetime
import hashlib
import io
import os

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


def _scan_directory(root: str) -> list[str]:
    """Return sorted list of absolute paths for all supported media files under *root*."""
    results = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            if ext in SUPPORTED_EXTS:
                results.append(os.path.join(dirpath, fname))
    return sorted(results)


@shared_task(
    bind=True,
    soft_time_limit=3600,  # 1 h per scan — raise SoftTimeLimitExceeded on timeout
    time_limit=3660,
)
def scan_library(self, library_id: int):
    """Walk an ExternalLibrary's directory and import any new media files.

    Progress is reported via ``self.update_state`` so the API endpoint can
    expose it to the client; the library row is also updated in-place.
    """
    from celery.exceptions import SoftTimeLimitExceeded
    from flask import current_app
    from sqlalchemy.exc import IntegrityError
    from Onani.models import ExternalLibrary, ExternalLibraryFile, Post
    from Onani.models.post import PostRating
    from Onani.services.posts import create_post
    from Onani.services.files import get_file_data, get_video_data, detect_video_format

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
    # Phase 1: discover all files on disk
    # -----------------------------------------------------------------------
    try:
        disk_paths = set(_scan_directory(library.path))
    except SoftTimeLimitExceeded:
        library.last_scan_status = "FAILED"
        library.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return {"error": "Scan timed out during directory walk."}
    except Exception as e:
        library.last_scan_status = "FAILED"
        library.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return {"error": f"Directory walk failed: {e}"}

    logs.append(f"Discovered {len(disk_paths)} media file(s) on disk.")
    _update("PROGRESS", {"library_id": library_id, "logs": logs})

    # -----------------------------------------------------------------------
    # Phase 2: reconcile with existing ExternalLibraryFile records
    # -----------------------------------------------------------------------
    now = datetime.datetime.now(datetime.timezone.utc)
    existing: dict[str, ExternalLibraryFile] = {
        f.file_path: f
        for f in library.files.all()
    }

    # Mark files that have disappeared from disk as MISSING.
    for path, rec in existing.items():
        if path not in disk_paths and rec.status not in ("MISSING", "IMPORTED"):
            rec.status = "MISSING"

    # Create PENDING records for new paths; refresh last_seen for known ones.
    new_paths = []
    retry_paths = []  # FAILED files get a retry on each scan
    for path in disk_paths:
        if path in existing:
            rec = existing[path]
            rec.last_seen_at = now
            if rec.status == "FAILED":
                rec.status = "PENDING"
                retry_paths.append(path)
        else:
            rec = ExternalLibraryFile(
                library_id=library_id,
                file_path=path,
                first_seen_at=now,
                last_seen_at=now,
                status="PENDING",
            )
            db.session.add(rec)
            new_paths.append(path)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logs.append(f"Warning: could not persist file discovery records: {e}")

    logs.append(
        f"New: {len(new_paths)}, retrying failed: {len(retry_paths)}, "
        f"missing: {sum(1 for r in existing.values() if r.status == 'MISSING')}."
    )
    _update("PROGRESS", {"library_id": library_id, "logs": logs})

    # -----------------------------------------------------------------------
    # Phase 3: import PENDING files
    # -----------------------------------------------------------------------
    pending = (
        ExternalLibraryFile.query
        .filter_by(library_id=library_id, status="PENDING")
        .order_by(ExternalLibraryFile.file_path)
        .all()
    )

    total_pending = len(pending)
    imported_count = 0
    failed_count = 0
    skipped_count = 0

    # Resolve the importer User for post ownership (the library owner).
    from Onani.models import User
    owner = User.query.get(library.owner_id) if library.owner_id else None

    # Parse default tags once.
    default_tags: set = set(
        t.strip() for t in (library.default_tags or "").split() if t.strip()
    )

    # Validate default rating.
    valid_ratings = {r.value for r in PostRating}
    default_rating = library.default_rating if library.default_rating in valid_ratings else "q"

    for idx, file_rec in enumerate(pending):
        _update("PROGRESS", {
            "library_id": library_id,
            "current": idx,
            "total": total_pending,
            "logs": logs,
        })

        path = file_rec.file_path
        if not os.path.isfile(path):
            file_rec.status = "MISSING"
            db.session.commit()
            skipped_count += 1
            continue

        try:
            # Compute hash first to detect duplicates without a full import.
            sha = _sha256_file(path)
            file_rec.sha256_hash = sha

            # Check for a duplicate post by hash.
            existing_post = Post.query.filter_by(sha256_hash=sha).first()
            if existing_post:
                file_rec.status = "IMPORTED"
                file_rec.post_id = existing_post.id
                file_rec.imported_at = now
                file_rec.error = None
                db.session.commit()
                skipped_count += 1
                logs.append(
                    f"[{idx+1}/{total_pending}] Skipped (duplicate hash): {os.path.basename(path)}"
                )
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
                source="",
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
                imported_from=path,
            )

            file_rec.status = "IMPORTED"
            file_rec.post_id = post.id
            file_rec.sha256_hash = hash_sha256
            file_rec.imported_at = datetime.datetime.now(datetime.timezone.utc)
            file_rec.error = None
            db.session.commit()

            imported_count += 1
            logs.append(
                f"[{idx+1}/{total_pending}] Imported: {os.path.basename(path)} → post #{post.id}"
            )

        except SoftTimeLimitExceeded:
            db.session.rollback()
            library.last_scan_status = "FAILED"
            library.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
            db.session.commit()
            return {
                "library_id": library_id,
                "error": "Scan timed out during import.",
                "imported": imported_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "logs": logs,
            }

        except Exception as e:
            db.session.remove()
            file_rec_fresh = ExternalLibraryFile.query.get(file_rec.id)
            if file_rec_fresh:
                file_rec_fresh.status = "FAILED"
                file_rec_fresh.error = str(e)
                db.session.commit()
            failed_count += 1
            logs.append(
                f"[{idx+1}/{total_pending}] Failed: {os.path.basename(path)}: {e}"
            )

    # -----------------------------------------------------------------------
    # Phase 4: finalise
    # -----------------------------------------------------------------------
    library_fresh = ExternalLibrary.query.get(library_id)
    if library_fresh:
        library_fresh.last_scan_at = datetime.datetime.now(datetime.timezone.utc)
        library_fresh.last_scan_status = "FAILED" if failed_count and not imported_count else "SUCCESS"
        library_fresh.last_scan_task_id = self.request.id
        db.session.commit()

    summary = (
        f"Scan complete. Imported: {imported_count}, "
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
