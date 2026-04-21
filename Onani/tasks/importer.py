# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-02 01:41:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 15:01:44

import os
import tempfile

from celery import shared_task

from . import db


def _safe_update_state(task, state: str, meta: dict) -> None:
    """Best-effort task progress updates.

    Celery backends can intermittently fail (e.g. transient DB/libpq errors).
    Progress reporting should not abort a long-running import task.
    """
    try:
        task.update_state(state=state, meta=meta)
    except Exception:
        # Keep import processing alive even if progress persistence fails.
        pass


def _dispatch_next_queued(domain: str) -> None:
    """Dispatch the oldest QUEUED ImportJob for *domain*, if any.

    Called at the end of ``import_post`` so that imports from the same
    extractor domain run serially rather than concurrently.

    Uses SELECT FOR UPDATE SKIP LOCKED to be safe under multiple Celery workers.
    """
    if not domain:
        return
    try:
        from Onani.models.import_job import ImportJob
        job = (
            ImportJob.query
            .filter_by(domain=domain, status="QUEUED")
            .order_by(ImportJob.created_at.asc())
            .with_for_update(skip_locked=True)
            .first()
        )
        if not job:
            db.session.rollback()  # release the advisory lock
            return
        cookies_content = (job.queue_meta or {}).get("cookies_content")
        job.status = "PENDING"
        db.session.commit()
        import_post.apply_async(
            args=[job.url, job.user_id, cookies_content],
            task_id=job.task_id,
        )
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


@shared_task(
    bind=True,
    soft_time_limit=900,   # 15 min — raises SoftTimeLimitExceeded, allowing cleanup
    time_limit=960,        # 16 min — hard kill if soft limit is ignored
)
def import_post(self, post_url: str, importer_id: int, cookies_content: str = None):
    import datetime
    from celery.exceptions import SoftTimeLimitExceeded
    from Onani.importers import get_all_posts, save_imported_post, ImportedPostSchema
    from Onani.importers.gallery_dl_importer import is_supported, GalleryDLTimeoutError, GalleryDLAbortError
    from Onani.models import Collection

    # Discard any stale session/connection from a previous task or failed request.
    # db.session.remove() returns the connection to the pool and ensures the next
    # operation gets a clean connection (important in long-running Celery workers).
    db.session.remove()

    logs = []
    logs.append(f"Fetching metadata from {post_url}...")
    _safe_update_state(self, state="PROGRESS", meta={
        "current": 0, "total": 0, "logs": logs, "url": post_url,
    })

    # Write cookies to a temp file if provided
    cookies_path = None
    if cookies_content:
        try:
            fd, cookies_path = tempfile.mkstemp(suffix=".txt", prefix="gdl_cookies_")
            os.write(fd, cookies_content.encode("utf-8"))
            os.close(fd)
            logs.append("Using uploaded cookies file.")
        except Exception as e:
            logs.append(f"Warning: could not write cookies file: {e}")
            cookies_path = None

    result = None
    # Determine if this is a community-site import (Reddit, RedGifs, etc.)
    # where the artist/author is the actual content creator
    from urllib.parse import urlparse
    parsed = urlparse(post_url)
    domain = parsed.hostname or ""
    is_community = any(x in domain for x in ["reddit", "redgifs", "twitter", "x.com", "instagram", "pixiv"])

    try:
        try:
            imported_posts = get_all_posts(post_url, cookies_path=cookies_path)
        except GalleryDLTimeoutError as e:
            result = {"error": str(e), "logs": logs + [f"Error: {e}"], "url": post_url}
            return result
        except GalleryDLAbortError as e:
            result = {"error": str(e), "logs": logs + [f"Error: {e}"], "url": post_url}
            return result
        except SoftTimeLimitExceeded:
            msg = f"Import timed out for {post_url} (Celery soft time limit)."
            result = {"error": msg, "logs": logs + [f"Error: {msg}"], "url": post_url}
            return result
        except Exception as e:
            result = {"error": f"Failed to fetch: {e}", "logs": [f"Error: {e}"], "url": post_url}
            return result

        if not imported_posts:
            # Distinguish between unsupported URLs and supported-but-empty results
            if not is_supported(post_url):
                msg = f"URL is not supported by any importer: {post_url}"
            else:
                msg = (
                    f"No posts returned for URL: {post_url}. "
                    "The page may be empty, private, or rate-limited."
                )
            result = {"error": msg, "logs": logs, "url": post_url}
            return result

        total = len(imported_posts)
        results = []
        saved_post_ids = []  # IDs of successfully imported posts (avoids detached-instance)
        logs.append(f"Found {total} post(s). Starting import...")

        for i, imported_post in enumerate(imported_posts):
            try:
                post = save_imported_post(imported_post, importer_id, cookies_path=cookies_path, is_community_import=is_community)
                result = ImportedPostSchema().dump(imported_post)
                result["post_id"] = post.id
                result["thumbnail_url"] = post.thumbnail(size="large")
                results.append(result)
                saved_post_ids.append(post.id)
                logs.append(f"[{i+1}/{total}] Imported: post #{post.id}")
            except Exception as e:
                # Use remove() instead of rollback() — after a DB error (e.g. FK
                # violation, connection error) the PostgreSQL transaction is in an
                # aborted state. rollback() resets the ORM but can leave the
                # underlying connection poisoned. remove() discards the session and
                # returns the connection to the pool, guaranteeing the next post
                # starts with a clean connection.
                db.session.remove()
                results.append({"error": str(e), "file_url": imported_post.file_url})
                logs.append(f"[{i+1}/{total}] Skipped: {e}")

            _safe_update_state(self, state="PROGRESS", meta={
                "current": i + 1,
                "total": total,
                "logs": logs,
                "url": post_url,
            })

        # If any post carries a collection_name, create/find an Onani collection
        # and add all successfully saved posts to it.
        collection_info = None
        collection_name = next(
            (p.collection_name for p in imported_posts if p.collection_name), None
        )
        if collection_name and saved_post_ids:
            try:
                from sqlalchemy.exc import IntegrityError
                from Onani.models import Post
                collection = Collection.query.filter_by(
                    title=collection_name, creator=importer_id
                ).first()
                if collection is None:
                    collection = Collection(
                        title=collection_name,
                        description=f"Imported from {post_url}",
                        creator=importer_id,
                    )
                    db.session.add(collection)
                    try:
                        with db.session.begin_nested():
                            db.session.flush()
                    except IntegrityError:
                        # Another worker created the same collection concurrently.
                        collection = Collection.query.filter_by(
                            title=collection_name, creator=importer_id
                        ).first()

                # Re-query posts by ID so we have fresh session-bound instances
                # (saved_post_ids are plain ints — immune to session.remove() calls).
                existing_ids = {p.id for p in collection.posts}
                for post_id in saved_post_ids:
                    if post_id not in existing_ids:
                        post = db.session.get(Post, post_id)
                        if post:
                            collection.posts.append(post)

                db.session.commit()
                collection_info = {"id": collection.id, "title": collection.title}
                logs.append(f"Added {len(saved_post_ids)} post(s) to collection '{collection_name}' (#{collection.id}).")
            except Exception as e:
                db.session.rollback()
                logs.append(f"Warning: could not create collection: {e}")

        result = {
            "posts": results,
            "count": len(results),
            "url": post_url,
            "logs": logs,
            "collection": collection_info,
        }
        return result
    finally:
        if cookies_path:
            try:
                os.unlink(cookies_path)
            except OSError:
                pass
        # Sync terminal state back to the ImportJob DB record (if one exists).
        # This ensures scheduled imports and any task that completes without a
        # polling client still updates the history.
        if result is not None:
            try:
                from Onani.models.import_job import ImportJob
                job_rec = ImportJob.query.filter_by(task_id=self.request.id).first()
                if job_rec and job_rec.status not in ("SUCCESS", "FAILURE", "REVOKED"):
                    job_rec.status = "FAILURE" if result.get("error") else "SUCCESS"
                    job_rec.result = result
                    job_rec.finished_at = datetime.datetime.now(datetime.timezone.utc)
                    db.session.commit()
            except Exception:
                db.session.rollback()
        # Dispatch the next queued job for this domain (if any) so that
        # imports from the same extractor run serially.
        from urllib.parse import urlparse as _urlparse
        _domain = _urlparse(post_url).hostname or ""
        _dispatch_next_queued(_domain)
