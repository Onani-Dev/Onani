# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-20 01:04:40
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-08-08 19:16:30
from flask import redirect, render_template, request, url_for
from flask_login import current_user
from Onani.controllers import (
    create_avatar,
    create_ban,
    delete_ban,
    permissions_required,
)
from Onani.controllers.utils import flash_form_errors
from Onani.forms import (
    AccountPlatformForm,
    AccountProfileForm,
    AccountSettingsForm,
    AccountBanForm,
)
from Onani.models import Ban, Post, Tag
from Onani.models.schemas.ban import BanSchema

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

    # Flash all the errors that may be present in the form
    flash_form_errors(form)

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
    # Flash all the errors that may be present in the form
    flash_form_errors(form)

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

    # Flash all the errors that may be present in the form
    flash_form_errors(form)

    return redirect(url_for("main.get_user", user_id=current_user.id))


@main.route("/settings/ban/", methods=["POST"])

# Make it permissionable


def ban_user():
    form = AccountBanForm()
    if form.validate():
        ban = create_ban(
            user_id=form.user_id.data,
            expires=form.banned_until.data,
            reason=form.ban_reason.data,
            delete_posts=None,
            hide_posts=None,
        )

        return BanSchema().dump(ban)

    # Flash all the errors that may be present in the form
    flash_form_errors(form)

    return redirect(url_for("main.get_user", user_id=current_user.id))
