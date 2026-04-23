# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-25 13:41:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-25 15:40:25

from typing import List, Optional

from flask import current_app
from onani.models import Post, Tag
from sqlalchemy import distinct, func

from . import db


def query_posts(
    tags: Optional[List[str]] = None,
    show_hidden: bool = False,
):
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

    return posts
