# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-20 01:04:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 03:02:06
from flask import redirect, render_template, request
from flask_login import current_user
from Onani.forms import AccountProfileForm, AccountSettingsForm
from Onani.models import Ban, Post, Tag

from . import db, main


@main.route("/settings/account/", methods=["POST"])
def settings_account():
    form = AccountSettingsForm()
    if form.validate():
        if form.username.data:
            current_user.username = form.username.data

        if form.email.data:
            current_user.email = form.email.data

        if form.new_password.data and current_user.check_password(
            form.current_password.data
        ):
            current_user.set_password(form.new_password.data)

        db.session.commit()

    return redirect(f"/users/{current_user.id}?t=settings")


@main.route("/settings/profile/", methods=["POST"])
def settings_profile():
    form = AccountProfileForm()
    if form.validate():
        if form.biography.data:
            current_user.settings.biography = form.biography.data

        if form.profile_picture.data:
            print(form.profile_picture.data)

        db.session.commit()

    return redirect(f"/users/{current_user.id}?t=settings")
