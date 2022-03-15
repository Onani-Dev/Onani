# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-16 00:53:28
from flask import render_template, request
from Onani.models import Ban, Post, Tag

from . import main, db


@main.route("/")
@main.route("/posts/")
def posts():
    # Get the tags from the request args
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None

    # Get the page, will default to 0 if there is no args
    page = request.args.get("p", "0")

    # Convert the page to an int if it is a digit, if it is not, default to 0
    page = int(page) if page.isdigit() else 0

    # if there is tags get the posts by them
    if tags:
        posts = Post.query.filter(
            Post.tags.any(Tag.posts.any(Tag.name.in_(tags)))
        ).paginate(per_page=36, page=page, error_out=False)
    else:
        posts = Post.query.order_by(Post.id.desc()).paginate(
            per_page=36, page=page, error_out=False
        )

    # Get the tags sorted by the post count
    tags = Tag.query.order_by(Tag.post_count.desc(), Tag.type.desc()).limit(25).all()

    # render the index template
    return render_template(
        "/index.jinja2",
        tags=tags,
        posts=posts,
    )
