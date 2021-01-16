# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 22:04:59
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-17 03:05:50

import html
import random
import re
import string
from datetime import datetime, timedelta

from flask import jsonify
from flask_login import LoginManager, current_user

from .. import login_manager
from ..models import Ban, Tag, User, UserPermissions, user_schemas
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
    # for user in User.query.all():
    #     print(user.username, user.password_hash, str(user.permissions))

    tag1 = Tag(name="".join([random.choice(string.ascii_letters) for _ in range(32)]))
    tag1.save_to_db()

    user.tag_blacklist.append(tag1)
    db.session.commit()

    tag2 = Tag(name="".join([random.choice(string.ascii_letters) for _ in range(32)]))
    tag1.aliases.append(tag2)
    tag2.save_to_db()

    user.tag_blacklist.append(tag2)

    db.session.commit()

    ban = Ban(
        user=user.id, reason="Cockhead", expires=datetime.utcnow() + timedelta(days=50)
    )
    ban.save_to_db()

    print(ban.has_expired)

    print(user.tag_blacklist)
    print(type(tag1.aliases))

    return user_schemas.jsonify(User.query.all())
