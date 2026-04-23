# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 12:43:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:51:32
from onani.models import User, UserRoles

from . import db


def create_user(
    username: str,
    password: str,
    email: str = None,
    role: UserRoles = UserRoles.MEMBER,
) -> User:
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    user.save_to_db()
    return user
