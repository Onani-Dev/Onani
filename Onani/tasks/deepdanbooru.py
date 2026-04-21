# -*- coding: utf-8 -*-
import datetime

from celery import shared_task

from . import db


@shared_task(bind=True, soft_time_limit=7200, time_limit=7260)
def deepdanbooru_tag_all_posts(self):
    from flask import current_app

    from Onani.models import Post
    from Onani.services.deepdanbooru import (
        DeepDanbooruUnavailableError,
        apply_suggested_tags_to_post,
        suggest_tags_for_post,
    )

    db.session.remove()

    def _update(state: str, meta: dict):
        try:
            self.update_state(state=state, meta=meta)
        except Exception:
            pass

    posts = Post.query.order_by(Post.id.asc()).all()
    logs = [f"Starting DeepDanbooru tagging for {len(posts)} post(s)."]
    processed = 0
    updated_posts = 0
    added_tags = 0
    skipped = 0
    failed = 0

    for index, post in enumerate(posts, start=1):
        _update("PROGRESS", {
            "current": index - 1,
            "total": len(posts),
            "logs": logs,
        })
        try:
            suggestions = suggest_tags_for_post(post, current_app.config)
            delta = apply_suggested_tags_to_post(
                post,
                [item["tag"] for item in suggestions],
                tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                post_min_tags=current_app.config["POST_MIN_TAGS"],
            )
            db.session.commit()
            processed += 1
            if delta:
                updated_posts += 1
                added_tags += delta
                logs.append(f"[{index}/{len(posts)}] Post #{post.id}: added {delta} tag(s).")
            else:
                skipped += 1
        except DeepDanbooruUnavailableError as exc:
            db.session.rollback()
            return {
                "error": str(exc),
                "processed": processed,
                "updated_posts": updated_posts,
                "added_tags": added_tags,
                "skipped": skipped,
                "failed": failed,
                "logs": logs,
            }
        except ValueError as exc:
            db.session.rollback()
            skipped += 1
            logs.append(f"[{index}/{len(posts)}] Post #{post.id}: skipped ({exc}).")
        except Exception as exc:
            db.session.rollback()
            failed += 1
            logs.append(f"[{index}/{len(posts)}] Post #{post.id}: failed ({exc}).")

    summary = (
        f"DeepDanbooru finished at {datetime.datetime.now(datetime.timezone.utc).isoformat()} "
        f"for {processed} processed post(s): updated {updated_posts}, added {added_tags} tag(s), "
        f"skipped {skipped}, failed {failed}."
    )
    logs.append(summary)
    return {
        "processed": processed,
        "updated_posts": updated_posts,
        "added_tags": added_tags,
        "skipped": skipped,
        "failed": failed,
        "logs": logs,
    }