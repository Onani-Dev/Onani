# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 21:55:00

from flask import abort, render_template, request
from flask_login import current_user, login_required
from Onani.models import Tag, User

from . import main


@main.route("/users")
@login_required
def users():
    page = request.args.get("p", "0")

    # Convert the page to an int if it is a digit, if it is not, default to 0
    page = int(page) if page.isdigit() else 0
    users = User.query.order_by(User.id.desc()).paginate(
        per_page=35, page=page, error_out=False
    )

    tags = Tag.query.order_by(Tag.post_count.desc()).limit(25)

    return render_template(
        "/users.jinja2",
        users=users,
        tags=tags,
    )


@main.route("/users/<user_id>")
@login_required
def user(user_id):
    # Check if it is a valid number
    if not user_id.isdigit():
        # abort, it's not a number
        abort(404)

    # Convert to integer
    user_id = int(user_id)

    # Check If the user's id is the same as the logged in user
    if user_id == current_user.id:
        # We can save a database query by using the currently logged in user object
        user = current_user

    else:
        # Query for the user, if not found throw a 404
        user = User.query.filter_by(id=user_id).first_or_404()

    # Get the tags sorted by the post count
    tags = Tag.query.order_by(Tag.post_count.desc()).limit(25)

    # Render the user page
    return render_template(
        "/profile.jinja2",
        user=user,
        tags=tags,
    )
