# -*- coding: utf-8 -*-
from .. import csrf, db, limiter, login_manager
from .api import main_api
from Onani.models import User


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(login_id=user_id).first()
    if not user:
        return None
    return None if user.ban else user


@login_manager.request_loader
def request_loader(request):
    if api_key := request.headers.get("Authorization"):
        user = User.query.filter_by(api_key=api_key).first()
        if not user:
            return None
        return None if user.ban else user
    return None

