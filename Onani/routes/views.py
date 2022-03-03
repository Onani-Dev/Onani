# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 22:04:59
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-04 03:44:28

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
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None
    page = request.args.get("p", "0")
    page = int(page) if page.isdigit() else 0
    posts = Post.query.all()
    tags = Tag.query.all()
    return render_template(
        "/index.jinja2",
        tags=tags,
        posts=posts,
    )


@main.route("/users/")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    if user_id is not None:
        try:
            user_id = int(user_id)
        except Exception:
            abort(404)
        if user_id == current_user.id:
            user = current_user
        else:
            User.query.filter_by(id=user_id).first_or_404()
        return render_template(
            "/profile.jinja2",
            user=user,
            tags=Tag.query.all(),
        )
    return "Sorry nothing"


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
