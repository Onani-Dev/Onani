# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 22:04:59
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 01:40:36

import html
import random
import re
import string
import traceback
from datetime import datetime, timedelta

from flask import abort, jsonify, render_template, request
from flask_login import LoginManager, current_user, login_required
from Onani.models.schemas import UserSchema

from .. import login_manager
from ..models import Ban, Post, Tag, User, UserPermissions
from . import db, main


@main.app_errorhandler(Exception)
def error_handler(e):
    print(traceback.print_tb(e.__traceback__))  # DEBUG
    return str(e)


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


@main.route("/users/")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    # Check if the user id is in the URL
    if user_id is None:

        return "Sorry nothing"
    # Check if it is a valid number
    if not user_id.isdigit():
        # abort, it's not a number
        abort(404)

    # Convert to integer
    user_id = int(user_id)

    # Check If the user's id is the same as the logged in user
    if user_id == current_user.id:
        # We can save a database query by using the currently logged in user object
        user = current_user

    else:
        # Query for the user, if not found throw a 404
        user = User.query.filter_by(id=user_id).first_or_404()

    # Get the tags sorted by the post count
    tags = Tag.query.order_by(Tag.post_count.desc()).limit(25)

    # Render the user page
    return render_template(
        "/profile.jinja2",
        user=user,
        tags=tags,
    )


@main.route("/test")
def test():
    user_schema = UserSchema(
        exclude=["password_hash", "api_key", "email", "tag_blacklist", "ban"],
        many=True,
    )
    return jsonify(user_schema.dump(User.query.all()))


# Easter eggs
@main.route("/fun")
def sonic_fun():
    return render_template("/fun.jinja2")
