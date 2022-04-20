# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-20 15:59:31
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-20 16:11:55
# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:48:33
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-03 17:43:23

from functools import wraps
from typing import List, Union

from flask import abort
from flask_login import current_user
from Onani.models import UserPermissions


def permissions_required(permissions: Union[UserPermissions, List[UserPermissions]]):
    """A decorator for requiring certain permissions to access an endpoint on flask.

    Args:
        permissions (Union[UserPermissions, List[UserPermissions]]): The permissions to check the current user for
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Non authenticated users have no permissions
            if not current_user.is_authenticated:
                abort(403)

            # Check if permissions are a list an iterate through them
            if isinstance(permissions, list):
                for p in permissions:
                    if p not in current_user.permissions:
                        # User doesn't have these permissions
                        abort(403)
            # Check for a single permission
            elif permissions not in current_user.permissions:
                abort(403)

            # Return the function.
            return func(*args, **kwargs)

        return wrapper

    return decorator
