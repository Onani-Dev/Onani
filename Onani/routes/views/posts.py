# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-19 13:44:09

from flask import abort, current_app, render_template, request
from flask_login import current_user
from Onani.controllers.utils import get_page
from Onani.forms import EditForm
from Onani.models import Post, Tag
from sqlalchemy import distinct, func

from . import main


@main.route("/posts/")
def post_index():
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

    # render the index template
    return render_template(
        "/routes/posts/index.jinja2",
        posts=posts,
    )


@main.route("/posts/<post_id>")
def post_page(post_id=None):
    # Check if post id is supplied and a valid number
    if not post_id or not post_id.isdigit():
        # abort, it's not valid or a number
        abort(404)

    # Get the post if it exists, if not throw a 404 eror
    post: Post = Post.query.filter_by(id=post_id).first_or_404()

    # Create the edit form
    edit_form = EditForm()

    # Make the default values the current post values
    edit_form.description.data = post.description
    edit_form.source.data = post.source
    edit_form.rating.data = post.rating.value

    # Add the tags and old_tags to the form
    edit_form.tags.data = " ".join(tag.text_format for tag in post.tags)
    edit_form.old_tags.data = " ".join(tag.text_format for tag in post.tags)

    # render the template
    return render_template("/routes/posts/post.jinja2", post=post, edit_form=edit_form)
