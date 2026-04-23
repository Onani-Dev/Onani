# -*- coding: utf-8 -*-
"""Celery tasks for bulk thumbnail generation."""
import datetime
import os

from celery import shared_task

from . import db


@shared_task(bind=True, soft_time_limit=7200, time_limit=7260)
def generate_all_thumbnails(self):
    """Pre-generate every thumbnail size and sample image for all posts.

    Skips files that already have an up-to-date cached thumbnail.
    Reports progress via Celery task state so the admin UI can poll it.
    """
    from flask import current_app

    from Onani.models import Post
    from Onani.services.files import (
        build_cached_image_variant,
        cached_thumbnail_path,
        create_video_thumbnail,
        ensure_shard_dir,
        shard_path,
    )

    db.session.remove()

    VIDEO_FORMATS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
    SIZES = [50, 150, 350, 500]

    def _update(state: str, meta: dict):
        try:
            self.update_state(state=state, meta=meta)
        except Exception:
            pass

    images_dir = current_app.config["IMAGES_DIR"]
    posts = Post.query.order_by(Post.id.asc()).all()
    total = len(posts)
    logs = [f"Starting thumbnail generation for {total} post(s)."]
    generated = skipped = failed = 0

    for index, post in enumerate(posts, start=1):
        _update("PROGRESS", {
            "current": index - 1,
            "total": total,
            "logs": logs,
        })

        try:
            source_name = post.filename
            is_video = (post.file_type or "").lower() in VIDEO_FORMATS

            if is_video:
                stem = post.filename.rsplit(".", 1)[0]
                thumb_name = f"{stem}.jpg"
                thumb_path = shard_path(images_dir, thumb_name)
                if not os.path.isfile(thumb_path):
                    video_path = shard_path(images_dir, post.filename)
                    if not os.path.isfile(video_path):
                        failed += 1
                        logs.append(f"[{index}/{total}] Post #{post.id}: source file missing, skipped.")
                        continue
                    dest = ensure_shard_dir(images_dir, thumb_name)
                    if not create_video_thumbnail(video_path, dest):
                        failed += 1
                        logs.append(f"[{index}/{total}] Post #{post.id}: video thumbnail failed.")
                        continue
                source_name = thumb_name

            source_path = shard_path(images_dir, source_name)
            if not os.path.isfile(source_path):
                failed += 1
                logs.append(f"[{index}/{total}] Post #{post.id}: source file missing, skipped.")
                continue

            source_mtime = os.path.getmtime(source_path)
            thumb_variant = "videos" if is_video else "images"
            post_generated = 0
            post_skipped = 0

            for size_px in SIZES:
                cache_path = cached_thumbnail_path(
                    images_dir, thumb_variant, f"{size_px}x{size_px}", source_name
                )
                if os.path.isfile(cache_path) and os.path.getmtime(cache_path) >= source_mtime:
                    post_skipped += 1
                else:
                    build_cached_image_variant(
                        source_path=source_path,
                        cache_root=images_dir,
                        source_filename=source_name,
                        variant=thumb_variant,
                        max_width=size_px,
                        max_height=size_px,
                        quality=50,
                    )
                    post_generated += 1

            sample_cache = cached_thumbnail_path(images_dir, "sample", "800x2000", source_name)
            if os.path.isfile(sample_cache) and os.path.getmtime(sample_cache) >= source_mtime:
                post_skipped += 1
            else:
                build_cached_image_variant(
                    source_path=source_path,
                    cache_root=images_dir,
                    source_filename=source_name,
                    variant="sample",
                    max_width=800,
                    max_height=2000,
                    quality=80,
                )
                post_generated += 1

            generated += post_generated
            skipped += post_skipped

        except Exception as exc:
            failed += 1
            logs.append(f"[{index}/{total}] Post #{post.id}: error — {exc}.")

    summary = (
        f"Thumbnail generation finished at "
        f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} — "
        f"posts:{total} generated:{generated} skipped:{skipped} failed:{failed}."
    )
    logs.append(summary)
    return {
        "posts": total,
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "logs": logs,
    }
