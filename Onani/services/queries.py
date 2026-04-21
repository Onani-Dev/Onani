from typing import List, Optional

from Onani.models import Post, Tag
from Onani.models.post._post import post_tags as _post_tags
from sqlalchemy import distinct, func

from Onani import db


def query_posts(
    tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    show_hidden: bool = False,
):
    """Build a base SQLAlchemy query for posts with optional tag filtering.

    Args:
        tags: Filter to posts that have ALL of these tag names.
        exclude_tags: Exclude posts that have ANY of these tag names.
        show_hidden: Include posts flagged as hidden.
    """
    posts = Post.query

    if not show_hidden:
        posts = posts.filter(Post.hidden.is_(False))

    if tags:
        posts = (
            posts.join(Post.tags)
            .filter(Tag.name.in_(tags))
            .group_by(Post)
            .having(func.count(distinct(Tag.id)) == len(tags))
            .order_by(Post.id.desc())
        )
    else:
        posts = posts.order_by(Post.id.desc())

    if exclude_tags:
        # LEFT JOIN anti-join: avoids the NOT IN (SELECT …) plan which PostgreSQL
        # cannot use an index-only scan for when the subquery is large.
        excl_subq = (
            db.session.query(_post_tags.c.post_id)
            .join(Tag, Tag.id == _post_tags.c.tag_id)
            .filter(Tag.name.in_(exclude_tags))
            .distinct()
            .subquery()
        )
        posts = posts.outerjoin(excl_subq, Post.id == excl_subq.c.post_id).filter(
            excl_subq.c.post_id.is_(None)
        )

    return posts
