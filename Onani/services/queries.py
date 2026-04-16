# -*- coding: utf-8 -*-
from typing import List, Optional

from Onani.models import Post, Tag
from Onani.models.post.status import PostStatus
from sqlalchemy import distinct, func

from Onani import db


def query_posts(
    tags: Optional[List[str]] = None,
    show_hidden: bool = False,
    show_removed: bool = False,
):
    """Build a base SQLAlchemy query for posts with optional tag filtering.

    Args:
        tags: Filter to posts that have ALL of these tag names.
        show_hidden: Include posts flagged as hidden.
        show_removed: Include posts with status other than APPROVED/PENDING.
    """
    posts = Post.query

    if not show_hidden:
        posts = posts.filter(Post.hidden.is_(False))

    if not show_removed:
        posts = posts.filter(Post.status.in_([PostStatus.APPROVED, PostStatus.PENDING]))

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

    return posts
