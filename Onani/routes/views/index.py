# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 03:00:02
from flask import render_template, request
from Onani.models import Ban, Post, Tag

from . import main


@main.route("/")
@main.route("/posts/")
def posts():
    # Get the tags from the request args
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None

    # Get the page, will default to 0 if there is no args
    page = request.args.get("p", "0")

    # Convert the page to an int if it is a digit, if it is not, default to 0
    page = int(page) if page.isdigit() else 0

    # Get the posts with an offset times the page and with a limit of 36 per page
    posts = Post.query.order_by(Post.id.desc()).offset(36 * page).limit(36)

    # Get the tags sorted by the post count
    tags = Tag.query.order_by(Tag.post_count.desc()).limit(25)

    # render the index template
    return render_template(
        "/index.jinja2",
        tags=list(tags),
        posts=list(posts),
    )
