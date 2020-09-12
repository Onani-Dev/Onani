# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 13:23:02
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-12 16:22:30

from flask import (
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_login import current_user, login_required

from OnaniCore import *

from . import main, onaniDB


@main.route("/")
@main.route("/posts")
def posts():
    return render_template(
        "/index.html.jinja2",
        current_user=current_user,
        tags=onaniDB.get_tags(limit=25, sort="post_count"),
    )


@main.route("/users")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    if user_id is not None:
        if user_id == current_user.id:
            return current_user.username
        try:
            user_id = int(user_id)
        except:
            abort(404)
        user = onaniDB.get_user(id=user_id)
        return user.username + " " + user.permissions.string
    return NotImplemented
