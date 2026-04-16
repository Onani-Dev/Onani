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
        logs.append(f"Found {total} post(s). Starting import...")

        for i, imported_post in enumerate(imported_posts):
            try:
                post = save_imported_post(imported_post, importer_id)
                result = ImportedPostSchema().dump(imported_post)
                result["post_id"] = post.id
                results.append(result)
                logs.append(f"[{i+1}/{total}] Imported: post #{post.id}")
            except Exception as e:
                results.append({"error": str(e), "file_url": imported_post.file_url})
                logs.append(f"[{i+1}/{total}] Skipped: {e}")

            self.update_state(state="PROGRESS", meta={
                "current": i + 1,
                "total": total,
                "logs": logs,
                "url": post_url,
            })

        return {"posts": results, "count": len(results), "url": post_url, "logs": logs}
    finally:
        if cookies_path:
            try:
                os.unlink(cookies_path)
            except OSError:
                pass
