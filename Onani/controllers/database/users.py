# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 12:43:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 01:38:10
from Onani.models.user import User, UserPermissions, UserSettings

from . import db


def create_user(
    username: str,
    password: str,
    email: str = None,
    permissions: UserPermissions = UserPermissions.MEMBER,
) -> User:
    user = User(username=username, email=email, permissions=permissions)
    user.set_password(password)
    user.save_to_db()
    return user
