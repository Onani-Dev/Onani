# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:52:28
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 21:10:56

from Onani.models import User

from . import login_manager


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(login_id=user_id).first()
    if not user:
        return
    return None if user.ban else user


@login_manager.request_loader
def request_loader(request):
    if api_key := request.headers.get("Authorization"):
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return
        return None if user.ban else user
    return
