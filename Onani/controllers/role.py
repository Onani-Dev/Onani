# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:48:33
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 01:02:37

from functools import wraps

from flask import abort
from flask_login import current_user
from Onani.models import UserRoles


def role_required(role: UserRoles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role.value >= role.value:
                return func(*args, **kwargs)
            abort(403)

        return wrapper

    return decorator
