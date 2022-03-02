# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 22:04:59
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-03 01:38:36

import html
import random
import re
import string
import traceback
from datetime import datetime, timedelta

from flask import jsonify, render_template, request
from flask_login import LoginManager, current_user

from .. import login_manager
from ..models import Ban, Tag, User, UserPermissions, user_schemas
from . import db, main


@main.app_errorhandler(Exception)
def error_handler(e):
    print(traceback.print_tb(e.__traceback__))  # DEBUG
    return str(traceback.print_tb(e.__traceback__))


@login_manager.request_loader
def request_loader(request):
    if request.authorization:
        username, password = (
            request.authorization.username,
            request.authorization.password,
        )

        user = User.query.filter_by(username=username).first()

        if user.check_password(password):
            return user
    return

    # api_key = request.headers.get("Authorization")
    # if api_key:
    #     user = onaniDB.get_user(api_key=api_key)
    #     if user is None:
    #         return
    #     return user if not user.is_banned else None
    # return


@main.route("/")
@main.route("/posts/")
def posts():
    tags = request.args.get("tags").split(" ") if request.args.get("tags") else None
    page = request.args.get("p", "0")
    page = int(page) if page.isdigit() else 0
    posts = []
    return render_template(
        "/index.jinja2",
        tags=[],
        posts=posts,
    )


# Easter eggs
@main.route("/fun")
def sonic_fun():
    return render_template("/fun.jinja2")
