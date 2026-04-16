# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-19 12:46:08
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-24 14:08:43
from datetime import datetime

from flask import abort
from flask_login import current_user
from Onani.models import Ban, Post, User

from . import db


def create_ban(
    user_id: int, expires: datetime, reason: str, delete_posts: bool, hide_posts: bool
) -> Ban:
    """Create a ban against a user.

    Args:
        user_id (int): The user's ID to ban
        expires (datetime): The expiry of the ban
        reason (str): The reason for the ban
        delete_posts (bool): Delete the posts from that user
        hide_posts (bool): Hide the posts from that user (reversable)

    Returns:
        Ban: The new ban object
    """
    # Get the user
    user = User.query.filter_by(id=user_id).first()

    # Check if the user can even be banned
    if not user:
        abort(404, description="No user with that ID exists.")

    elif user.ban:
        abort(400, description="User is already banned.")

    elif user.id == current_user.id:
        abort(403, description="It's a horrible idea to ban yourself.")

    # Check the heirachy
    if current_user.role.value <= user.role.value:
        abort(
            403, description="Cannot ban this user, their role is the same or higher."
        )

    if delete_posts:
        from Onani.tasks.database import delete_user_posts
        delete_user_posts.delay(user.id)

    elif hide_posts:
        Post.query.filter_by(uploader_id=user.id).update({"hidden": True})

    ban = Ban(
        user=user.id,
        expires=expires,
        reason=reason,
        posts_hidden=hide_posts,
        posts_deleted=delete_posts,
    )

    db.session.add(ban)

    user.ban = ban

    db.session.commit()

    return ban


def delete_ban(user_id: int):
    user = User.query.filter_by(id=user_id).first()

    if not user:
        abort(404, description="No user with that ID exists.")

    elif not user.ban:
        abort(400, description="User is not banned.")

    if user.ban.posts_hidden:
        Post.query.filter_by(uploader_id=user.id).update({"hidden": False})

    db.session.delete(user.ban)
    db.session.commit()

    return user
