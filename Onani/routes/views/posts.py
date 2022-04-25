# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-25 18:18:09

from flask import abort, render_template, request, current_app
from flask_login import current_user
from Onani.models import Post, PostSchema, Tag
from sqlalchemy import func, distinct

from . import main


@main.route("/posts/")
@main.route("/posts/<post_id>")
def get_posts(post_id=None):
    if post_id:
        post = Post.query.filter_by(id=post_id).first_or_404()

        return render_template("/post.jinja2", post=post)

    # Get the tags from the request args
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None

    # Get the page, will default to 0 if there is no args
    page = request.args.get("p", "0")

    # Convert the page to an int if it is a digit, if it is not, default to 0
    page = int(page) if page.isdigit() else 0

    # if there is tags get the posts by them
    if tags:
        posts = (
            Post.query.join(Post.tags)
            .filter(Tag.name.in_(tags))
            .group_by(Post)
            .having(func.count(distinct(Tag.id)) == len(tags))
            .order_by(Post.id.desc())
            .paginate(
                per_page=current_app.config["PER_PAGE_POSTS"],
                page=page,
                error_out=False,
            )
        )
    else:
        posts = Post.query.order_by(Post.id.desc()).paginate(
            per_page=current_app.config["PER_PAGE_POSTS"], page=page, error_out=False
        )

    # render the index template
    return render_template(
        "/posts.jinja2",
        posts=posts,
    )
