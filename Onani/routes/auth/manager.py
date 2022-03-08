# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:52:28
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 02:54:33

from Onani.models import User

from . import login_manager


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return
    return user if not user.is_banned else None


@login_manager.request_loader
def request_loader(request):
    # Normal Login
    if request.authorization:
        username, password = (
            request.authorization.username,
            request.authorization.password,
        )

        user = User.query.filter_by(username=username).first()

        if user.check_password(password):
            return user if not user.is_banned else None

    if api_key := request.headers.get("Authorization"):
        user = User.query.filter_by(api_key=api_key).first()
        if user is None:
            return
        return user if not user.is_banned else None
    return
