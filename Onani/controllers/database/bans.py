# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-19 12:46:08
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-19 13:32:09
from datetime import datetime

from flask_login import current_user
from Onani.models import Ban, User

from . import db


def create_ban(user_id: int, expires: datetime, reason: str) -> Ban:
    """Create a ban against a user.

    Args:
        user_id (int): The user's ID to ban
        expires (datetime): The expiry of the ban
        reason (str): The reason for the ban

    Raises:
        ValueError: There is no user with the specified ID
        ValueError: There is already a ban on this user

    Returns:
        Ban: The new ban object
    """
    user = User.query.filter_by(id=user_id).first()

    if not user:
        raise ValueError("No user with that ID exists.")

    elif user.ban:
        raise ValueError("User is already banned.")

    elif user.id == current_user.id:
        raise ValueError("It's a horrible idea to ban yourself.")

    ban = Ban(
        user=User,
        expires=expires,
        reason=reason,
    )

    db.session.add(ban)

    user.ban = ban

    db.session.commit()

    return ban


def delete_ban(user_id: int):
    user = User.query.filter_by(id=user_id).first()

    if not user:
        raise ValueError("No user with that ID exists.")

    elif not user.ban:
        raise ValueError("User is not banned.")

    db.session.delete(user.ban)
    db.session.commit()

    return user
