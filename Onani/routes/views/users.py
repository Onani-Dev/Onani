# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 02:58:41

from flask import abort, render_template
from flask_login import current_user, login_required
from Onani.models import Tag, User

from . import main


@main.route("/users/")
@main.route("/users/<user_id>")
@login_required
def users(user_id=None):
    # Check if the user id is in the URL
    if user_id is None:

        return "Sorry nothing"
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
