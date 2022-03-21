# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 03:52:46

import html

from flask import abort, render_template, request
from flask_login import current_user
from Onani.forms import AccountProfileForm, AccountSettingsForm
from Onani.models import Post, Tag, User, UserSettings

from . import main


@main.route("/users/")
@main.route("/users/<user_id>")
# @login_required
def users(user_id=None):
    if not user_id:
        page = request.args.get("p", "0")

        # Convert the page to an int if it is a digit, if it is not, default to 0
        page = int(page) if page.isdigit() else 0
        users = User.query.order_by(User.post_count.desc()).paginate(
            per_page=10, page=page, error_out=False
        )

        return render_template(
            "/users.jinja2",
            users=users,
        )

    # Check if it is a valid number
    if not user_id.isdigit():
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

    page = request.args.get("p", "0")
    page = int(page) if page.isdigit() else 0
    posts = user.posts.order_by(Post.id.desc()).paginate(
        per_page=20, page=page, error_out=False
    )

    account_form = AccountSettingsForm()
    profile_form = AccountProfileForm()
    if user.settings.biography:
        profile_form.biography.data = html.unescape(user.settings.biography)

    # Render the user page
    return render_template(
        "/profile.jinja2",
        user=user,
        posts=posts,
        UserSettings=UserSettings,
        account_form=account_form,
        profile_form=profile_form,
    )
