# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-20 01:04:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-26 15:55:16
from flask import redirect, render_template, request, url_for
from flask_login import current_user
from Onani.controllers import create_avatar
from Onani.forms import AccountPlatformForm, AccountProfileForm, AccountSettingsForm
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
    return redirect(url_for("main.get_user", user_id=current_user.id))


@main.route("/settings/profile/", methods=["POST"])
def settings_profile():
    form = AccountProfileForm()
    if form.validate():
        if form.biography.data:
            current_user.settings.biography = form.biography.data

        if form.profile_picture.data:
            create_avatar(current_user, form.profile_picture.data)

        if form.profile_colour.data:
            current_user.settings.profile_colour = (
                form.profile_colour.data
            )  # TODO Validation of hex code

        db.session.commit()

    return redirect(url_for("main.get_user", user_id=current_user.id))


@main.route("/settings/platforms/", methods=["POST"])
def settings_platforms():
    form = AccountPlatformForm()
    if form.validate():
        current_user.settings.connections = {
            "twitter": form.twitter.data,
            "pixiv": form.pixiv.data,
            "patreon": form.patreon.data,
            "deviantart": form.deviantart.data,
            "discord": form.discord.data,
            "github": form.github.data,
        }

        db.session.commit()

    return redirect(url_for("main.get_user", user_id=current_user.id))
