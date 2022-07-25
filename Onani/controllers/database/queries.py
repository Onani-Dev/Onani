# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-25 13:41:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-25 15:40:25

from typing import List, Optional

from flask import current_app
from Onani.models import Post, Tag
from sqlalchemy import distinct, func

from Onani.models.post.status import PostStatus

from . import db


def query_posts(
    tags: Optional[List[str]] = None,
    show_hidden: bool = False,
    show_removed: bool = False,
):  # TODO Add logic for searching for dates etc and md5 etc etc idfk

    # Base filter
    posts = Post.query

    # Hide the hidden posts
    if not show_hidden:
        posts = posts.filter(Post.hidden.is_(False))

    # Hide the removed posts
    if not show_removed:
        # TODO Add logic to hide pending posts
        posts = posts.filter(Post.status.in_([PostStatus.APPROVED, PostStatus.PENDING]))

    # We're searching by tags
    if tags:
        posts = (
            posts.join(Post.tags)
            .filter(Tag.name.in_(tags))
            .group_by(Post)
            .having(func.count(distinct(Tag.id)) == len(tags))
            .order_by(Post.id.desc())
        )

    # We're getting all posts.
    else:
        posts = posts.order_by(Post.id.desc())

    return posts
