# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 13:23:02
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-11-01 18:16:00


from flask import (
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask.helpers import url_for
from flask_login import current_user, login_required
from OnaniCore import *

from . import main, onaniDB


@main.route("/")
@main.route("/posts/")
def posts():
    # Get the tags from the query string
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None

    # get page and turn into int
    page = request.args.get("p", "0")
    page = int(page) if page.isdigit() else 0

    # Add the posts to a list
    posts = list()
    for post in onaniDB.get_posts(limit=36, page=page, tags=tags):
        # Set default value to true
        add = True

        # iterate through current user blacklist
        for tag in current_user.settings.tag_blacklist:

            # If the tag is in there
            if tag in [x.name for x in post.tags]:
                # set add value to false and break from the loop
                add = False
                break

        # add post to list if true
        if add:
            posts.append(post)

    return render_template(
        "/index.jinja2",
        tags=onaniDB.get_tags(limit=25, sort="post_count"),
        posts=posts,
    )


@main.route("/collections/")
@main.route("/collections/<collection_id>")
def collections():
    return render_template(
        "/index.jinja2", tags=onaniDB.get_tags(limit=25, sort="post_count"),
    )


@main.route("/post/<post_id>")
def post_route(post_id):
    post = onaniDB.get_post(int(post_id))
    return redirect(post.file.full_path)


@main.route("/users/")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    if user_id is not None:
        if int(user_id) == current_user.id:
            user = current_user
        else:
            try:
                user_id = int(user_id)
                user = onaniDB.get_user(id=user_id)
            except:
                abort(404)
        return render_template(
            "/profile.jinja2",
            user=user,
            tags=onaniDB.get_tags(limit=25, sort="post_count"),
        )
    return "Sorry nothing"


@main.route("/upload/")
@login_required
def upload():
    return render_template(
        "/upload.jinja2", tags=onaniDB.get_tags(limit=25, sort="post_count"),
    )


# Easter eggs
@main.route("/fun")
def sonic_fun():
    return render_template("/fun.jinja2")
