# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-08-08 18:42:36

import html

from flask import abort, current_app, render_template, request
from flask_login import current_user, login_required
from Onani.controllers.utils import get_page
from Onani.forms import (
    AccountPlatformForm,
    AccountProfileForm,
    AccountSettingsForm,
    AccountBanForm,
)
from Onani.models import Post, User

from . import main


@main.route("/users/")
@login_required
def get_users():
    page = get_page()
    users = User.query.order_by(User.post_count.desc()).paginate(
        per_page=current_app.config["PER_PAGE_USERS"], page=page, error_out=False
    )

    return render_template(
        "/routes/users/index.jinja2",
        users=users,
    )


@main.route("/users/<user_id>")
def get_user(user_id=None):
    # Check if it is a valid number
    if not user_id or not user_id.isdigit():
        # abort, it's not a number
        abort(404)

    # Convert to integer
    user_id = int(user_id)

    # Check If the user's id is the same as the logged in user
    if not current_user.is_anonymous and user_id == current_user.id:
        # We can save a database query by using the currently logged in user object
        user = current_user

    else:
        # Query for the user, if not found throw a 404
        user = User.query.filter_by(id=user_id).first_or_404()

    page = get_page()
    posts = user.posts.order_by(Post.id.desc()).paginate(
        per_page=current_app.config["PER_PAGE_USER_POSTS"], page=page, error_out=False
    )

    account_form = AccountSettingsForm()
    profile_form = AccountProfileForm()
    platform_form = AccountPlatformForm()
    account_ban_form = AccountBanForm()

    if not current_user.is_anonymous and user_id == current_user.id:
        if user.settings.biography:
            profile_form.biography.data = html.unescape(user.settings.biography)

        if user.settings.connections.get("twitter"):
            platform_form.twitter.data = user.settings.connections.get("twitter")

        if user.settings.connections.get("pixiv"):
            platform_form.pixiv.data = user.settings.connections.get("pixiv")

        if user.settings.connections.get("patreon"):
            platform_form.patreon.data = user.settings.connections.get("patreon")

        if user.settings.connections.get("deviantart"):
            platform_form.deviantart.data = user.settings.connections.get("deviantart")

        if user.settings.connections.get("discord"):
            platform_form.discord.data = user.settings.connections.get("discord")

        if user.settings.connections.get("github"):
            platform_form.github.data = user.settings.connections.get("github")

    # Render the user page
    return render_template(
        "/routes/users/user.jinja2",
        user=user,
        posts=posts,
        account_form=account_form,
        account_ban_form=account_ban_form,
        platform_form=platform_form,
        profile_form=profile_form,
    )
