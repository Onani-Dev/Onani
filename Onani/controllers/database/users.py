# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 12:43:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 01:16:49
from Onani.models.user import User, UserRoles, UserSettings

from . import db


def create_user(
    username: str,
    password: str,
    email: str = None,
    role: UserRoles = UserRoles.MEMBER,
) -> User:
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    return user
