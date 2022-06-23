# -*- coding: utf-8 -*-
# @Author: dirt3009
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-06-23 20:59:45

from flask import abort, current_app, render_template, request
from flask_login import current_user
from Onani.controllers.utils import get_page
from Onani.forms import EditForm
from Onani.models import Post, Tag
from sqlalchemy import distinct, func

from . import main


@main.route("/collectionpage")
def collectionstest():
    # Get the tags from the request args
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None

    # Get the page
    page = get_page()

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

    return render_template("/routes/collections/collection.jinja2", posts=posts)
