# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:52:28
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-15 23:02:27

from Onani.models import User

from . import login_manager


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(login_id=user_id).first()
    if not user:
        return
    return user if not user.ban else None


@login_manager.request_loader
def request_loader(request):
    if api_key := request.headers.get("Authorization"):
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return
        return user if not user.ban else None
    return
