# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-02 01:41:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 15:01:44

import os
import tempfile

from celery import shared_task

from . import db


@shared_task(bind=True)
def import_post(self, post_url: str, importer_id: int, cookies_content: str = None):
    from Onani.importers import get_all_posts, save_imported_post, ImportedPostSchema
    from Onani.models import Collection, CollectionStatus

    # Discard any stale session/connection from a previous task or failed request.
    # db.session.remove() returns the connection to the pool and ensures the next
    # operation gets a clean connection (important in long-running Celery workers).
    db.session.remove()

    logs = []
    logs.append(f"Fetching metadata from {post_url}...")
    self.update_state(state="PROGRESS", meta={
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

    try:
        try:
            imported_posts = get_all_posts(post_url, cookies_path=cookies_path)
        except Exception as e:
            return {"error": f"Failed to fetch: {e}", "logs": [f"Error: {e}"], "url": post_url}

        if not imported_posts:
            return {"error": f"No importer found or no posts returned for URL: {post_url}", "logs": logs, "url": post_url}

        total = len(imported_posts)
        results = []
        saved_posts = []  # successfully imported Post objects
        logs.append(f"Found {total} post(s). Starting import...")

        for i, imported_post in enumerate(imported_posts):
            try:
                post = save_imported_post(imported_post, importer_id, cookies_path=cookies_path)
                result = ImportedPostSchema().dump(imported_post)
                result["post_id"] = post.id
                result["thumbnail_url"] = post.thumbnail(size="large")
                results.append(result)
                saved_posts.append(post)
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

            self.update_state(state="PROGRESS", meta={
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
        if collection_name and saved_posts:
            try:
                from sqlalchemy.exc import IntegrityError
                collection = Collection.query.filter_by(
                    title=collection_name, creator=importer_id
                ).first()
                if collection is None:
                    collection = Collection(
                        title=collection_name,
                        description=f"Imported from {post_url}",
                        creator=importer_id,
                        status=CollectionStatus.ACCEPTED,
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

                for post in saved_posts:
                    if not collection.posts.filter_by(id=post.id).first():
                        collection.posts.append(post)

                db.session.commit()
                collection_info = {"id": collection.id, "title": collection.title}
                logs.append(f"Added {len(saved_posts)} post(s) to collection '{collection_name}' (#{collection.id}).")
            except Exception as e:
                db.session.rollback()
                logs.append(f"Warning: could not create collection: {e}")

        return {
            "posts": results,
            "count": len(results),
            "url": post_url,
            "logs": logs,
            "collection": collection_info,
        }
    finally:
        if cookies_path:
            try:
                os.unlink(cookies_path)
            except OSError:
                pass
