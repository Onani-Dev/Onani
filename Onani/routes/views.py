# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 22:04:59
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-14 02:22:44

import html
import random
import re
import string

# from flask import request
from flask_login import LoginManager, current_user

from .. import login_manager
from ..models import Tag, User, UserPermissions
from . import db, main


@main.app_errorhandler(Exception)
def error_handler(e):
    return str(e)


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
def index():
    user = User(
        username="".join([random.choice(string.ascii_letters) for _ in range(32)]),
        email="".join([random.choice(string.ascii_letters) for _ in range(6)])
        + "@onanis.me",
    )
    user.set_password("Cumm1")
    user.save_to_db()
    for user in User.query.all():
        print(user.username, user.password_hash, str(user.permissions))

    tag = Tag(name="".join([random.choice(string.ascii_letters) for _ in range(32)]))
    tag.save_to_db()

    user.tag_blacklist.append(tag)
    user.commit()

    tag = Tag(name="".join([random.choice(string.ascii_letters) for _ in range(32)]))
    tag.save_to_db()

    user.tag_blacklist.append(tag)
    user.commit()

    print(user.tag_blacklist)
    return html.escape(str(user))
