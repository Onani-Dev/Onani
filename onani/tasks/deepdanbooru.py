# -*- coding: utf-8 -*-
import datetime

from celery import shared_task

from . import db


def _run_deepdanbooru_batch(self, scope: str):
    from flask import current_app

    from onani.models import Post, PostRating, Tag
    from onani.services.deepdanbooru import (
        DeepDanbooruUnavailableError,
        apply_suggested_tags_to_post,
        suggest_labels_for_post,
    )

    db.session.remove()

    def _update(state: str, meta: dict):
        try:
            self.update_state(state=state, meta=meta)
        except Exception:
            pass

    if scope == "all":
        posts = Post.query.order_by(Post.id.asc()).all()
        logs = [f"Starting DeepDanbooru tagging for {len(posts)} post(s)."]
    else:
        posts = (
            Post.query
            .join(Post.tags)
            .filter(Tag.name == "tag_request")
            .order_by(Post.id.asc())
            .all()
        )
        logs = [f"Starting DeepDanbooru tagging for {len(posts)} tag_request post(s)."]

    processed = 0
    updated_posts = 0
    added_tags = 0
    updated_ratings = 0
    skipped = 0
    failed = 0

    for index, post in enumerate(posts, start=1):
        _update("PROGRESS", {
            "current": index - 1,
            "total": len(posts),
            "logs": logs,
        })
        try:
            labels = suggest_labels_for_post(post, current_app.config)
            suggestions = labels["tags"]
            delta = apply_suggested_tags_to_post(
                post,
                [item["tag"] for item in suggestions],
                tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                post_min_tags=current_app.config["POST_MIN_TAGS"],
            )

            rating_changed = False
            inferred_rating = labels.get("rating")
            if inferred_rating:
                target_rating = PostRating(inferred_rating)
                if post.rating != target_rating:
                    post.rating = target_rating
                    rating_changed = True
                    updated_ratings += 1

            db.session.commit()
            processed += 1
            if delta or rating_changed:
                updated_posts += 1
                added_tags += delta
                if delta and rating_changed:
                    logs.append(
                        f"[{index}/{len(posts)}] Post #{post.id}: added {delta} tag(s), rating -> {inferred_rating}."
                    )
                elif delta:
                    logs.append(f"[{index}/{len(posts)}] Post #{post.id}: added {delta} tag(s).")
                else:
                    logs.append(f"[{index}/{len(posts)}] Post #{post.id}: rating -> {inferred_rating}.")
            else:
                skipped += 1
        except DeepDanbooruUnavailableError as exc:
            db.session.rollback()
            return {
                "error": str(exc),
                "processed": processed,
                "updated_posts": updated_posts,
                "added_tags": added_tags,
                "updated_ratings": updated_ratings,
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
        f"updated {updated_ratings} rating(s), "
        f"skipped {skipped}, failed {failed}."
    )
    logs.append(summary)
    return {
        "processed": processed,
        "updated_posts": updated_posts,
        "added_tags": added_tags,
        "updated_ratings": updated_ratings,
        "skipped": skipped,
        "failed": failed,
        "logs": logs,
    }


@shared_task(bind=True, soft_time_limit=7200, time_limit=7260)
def deepdanbooru_tag_all_posts(self):
    return _run_deepdanbooru_batch(self, scope="all")


@shared_task(bind=True, soft_time_limit=7200, time_limit=7260)
def deepdanbooru_tag_tag_request_posts(self):
    return _run_deepdanbooru_batch(self, scope="tag_request")