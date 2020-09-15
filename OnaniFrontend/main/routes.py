# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 13:23:02
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-15 16:57:25

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
@main.route("/posts/")
def posts():
    return render_template(
        "/index.jinja2", tags=onaniDB.get_tags(limit=25, sort="post_count"),
    )


@main.route("/collections/")
@main.route("/collections/<collection_id>")
def collections():
    return "Sorry nothing"


@main.route("/users/")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    if user_id is not None:
        if user_id == current_user.id:
            return current_user.username
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


@main.route("/edit_profile", methods=["POST"])
@login_required
def edit_profile():
    return render_template("/edit_profile.jinja2")


@main.route("/upload/")
@login_required
def upload():
    return "Sorry nothing"


# Easter eggs
@main.route("/fun")
def sonic_fun():
    return render_template("/fun.jinja2")
