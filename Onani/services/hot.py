# -*- coding: utf-8 -*-
"""Hot-posts scoring and retrieval service.

The hot score for a post is computed from:
- Recent view count (log-scaled, 3-day window)
- Unique recent commenter count (log-scaled, 3-day window)
- Post score / upvote ratio (log-scaled, small weight)
- Tag count (log-scaled, tiny bonus for well-tagged posts)
- Exponential time decay tuned so a normal post stays hot ~1 day and a
  really popular one can stay hot up to ~3 days.
- A small random noise component for variety.

Results are cached for 30 minutes.
"""
import datetime
import math
import random
from typing import List

from sqlalchemy import distinct, func

from Onani import db
from Onani.models.post._post import Post
from Onani.models.post.comment import PostComment
from Onani.models.post.view import PostView
from Onani.models.post.status import PostStatus

# How far back to look for "recent" activity (views / comments)
_RECENT_WINDOW_DAYS = 3

# Cache key and timeout (30 minutes)
_CACHE_KEY_PREFIX = "hot_posts"
_CACHE_TIMEOUT = 30 * 60

# How many hot posts to compute/return by default
DEFAULT_HOT_LIMIT = 20


def compute_hot_score(
    score: int,
    age_hours: float,
    recent_views: int,
    unique_commenters: int,
    tag_count: int,
) -> float:
    """Return a floating-point hot score for a post.

    The score is positive, higher is hotter.  Time decay means posts
    naturally fall off the list over time; the decay constant is scaled
    by the post's raw popularity so that truly popular posts stay hot
    for up to ~3 days while typical posts fade within ~1 day.

    Args:
        score: The net vote score (upvotes - downvotes) of the post.
        age_hours: How old the post is in hours.
        recent_views: Number of view events within the recent window.
        unique_commenters: Number of *distinct* users who commented
            within the recent window (multiple comments from the same
            user count as one).
        tag_count: Total number of tags on the post.

    Returns:
        float: Hot score — larger means hotter.
    """
    # Score factor: logarithmic so a high score doesn't completely
    # dominate, and a negative score drags a bit.
    score_factor = math.log10(max(abs(score), 1)) * (1.0 if score >= 0 else -0.5)

    # View factor (log-scaled)
    view_factor = math.log1p(recent_views)

    # Unique commenter factor (log-scaled; weighted more than views)
    comment_factor = math.log1p(unique_commenters)

    # Tag count bonus (tiny — just helps well-tagged posts a little)
    tag_factor = math.log1p(tag_count)

    # Raw popularity score
    raw = (
        score_factor * 0.3
        + view_factor * 1.0
        + comment_factor * 1.5
        + tag_factor * 0.2
    )

    # Time decay — base 24 h, scaled up to 72 h for very popular posts
    decay_hours = 24.0 * (1.0 + min(raw / 5.0, 2.0))
    time_decay = math.exp(-max(age_hours, 0.0) / decay_hours)

    # Small random noise for variety (0 – 0.3)
    noise = random.uniform(0.0, 0.3)

    return raw * time_decay + noise


def get_hot_posts(limit: int = DEFAULT_HOT_LIMIT) -> List[Post]:
    """Return a list of 'hot' posts, using a 30-minute cache.

    The cache stores only post IDs (so SQLAlchemy sessions don't go stale),
    and the posts are re-fetched from the DB on each call that hits the cache.

    Args:
        limit: Maximum number of posts to return.

    Returns:
        List[Post]: Posts ordered by hot score (highest first).
    """
    from Onani import cache

    cache_key = f"{_CACHE_KEY_PREFIX}:{limit}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        # Re-fetch posts in the original order using the cached IDs
        posts_by_id = {
            p.id: p
            for p in Post.query.filter(Post.id.in_(cached_ids)).all()
        }
        return [posts_by_id[pid] for pid in cached_ids if pid in posts_by_id]

    hot = _compute_hot_posts(limit)
    cache.set(cache_key, [p.id for p in hot], timeout=_CACHE_TIMEOUT)
    return hot


def _compute_hot_posts(limit: int) -> List[Post]:
    """Fetch posts and compute hot scores, returning the top *limit* posts."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=_RECENT_WINDOW_DAYS)

    # Only consider active (approved/pending), non-hidden posts
    posts: List[Post] = (
        Post.query.filter(
            Post.hidden.is_(False),
            Post.status.in_([PostStatus.APPROVED, PostStatus.PENDING]),
        ).all()
    )

    if not posts:
        return []

    # Bulk-fetch recent view counts keyed by post_id
    view_counts = dict(
        db.session.query(PostView.post_id, func.count(PostView.id))
        .filter(PostView.viewed_at >= cutoff)
        .group_by(PostView.post_id)
        .all()
    )

    # Bulk-fetch unique recent commenter counts keyed by post_id
    commenter_counts = dict(
        db.session.query(
            PostComment.post_id,
            func.count(distinct(PostComment.author_id)),
        )
        .filter(PostComment.created_at >= cutoff)
        .group_by(PostComment.post_id)
        .all()
    )

    scored = []
    for post in posts:
        uploaded_at = post.uploaded_at
        if uploaded_at is not None and uploaded_at.tzinfo is None:
            uploaded_at = uploaded_at.replace(tzinfo=datetime.timezone.utc)
        age_hours = (now - uploaded_at).total_seconds() / 3600 if uploaded_at else 0.0

        hs = compute_hot_score(
            score=post.score,
            age_hours=age_hours,
            recent_views=view_counts.get(post.id, 0),
            unique_commenters=commenter_counts.get(post.id, 0),
            tag_count=post.tags.count(),
        )
        scored.append((hs, post))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in scored[:limit]]


def record_view(post_id: int) -> None:
    """Record a single view event for the given post.

    Args:
        post_id: Primary key of the post being viewed.
    """
    view = PostView(post_id=post_id)
    db.session.add(view)
    db.session.commit()
