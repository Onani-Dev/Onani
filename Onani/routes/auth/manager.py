# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:52:28
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 13:33:22

from Onani.models import User
from flask import session, request, redirect, url_for, flash

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


@login_manager.unauthorized_handler
def unauthorized_redirect():
    session["return_url"] = request.path
    flash("You must login to do this.", "warning")
    return redirect(url_for("main.login"))
