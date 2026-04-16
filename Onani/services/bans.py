# -*- coding: utf-8 -*-
from datetime import datetime

from Onani.models import Ban, Post, User

from Onani import db


class BanError(ValueError):
    """Raised when a ban operation is invalid."""


def create_ban(
    actor: User,
    user_id: int,
    expires: datetime,
    reason: str,
    delete_posts: bool,
    hide_posts: bool,
) -> Ban:
    """Create a ban for the given user.

    Args:
        actor: The user performing the ban (used for permission checks).
        user_id: ID of the user to ban.
        expires: When the ban expires (None for permanent).
        reason: Ban reason text.
        delete_posts: Whether to delete the user's posts.
        hide_posts: Whether to hide the user's posts.

    Raises:
        LookupError: If the user does not exist.
        BanError: If the ban is invalid (already banned, self-ban, insufficient role).
    """
    user = User.query.filter_by(id=user_id).first()

    if not user:
        raise LookupError("No user with that ID exists.")
    if user.ban:
        raise BanError("User is already banned.")
    if user.id == actor.id:
        raise BanError("It's a horrible idea to ban yourself.")
    if actor.role.value <= user.role.value:
        raise BanError("Cannot ban this user — their role is the same or higher.")

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


def delete_ban(user_id: int) -> User:
    """Remove the active ban from a user.

    Raises:
        LookupError: If the user does not exist.
        BanError: If the user is not currently banned.
    """
    user = User.query.filter_by(id=user_id).first()

    if not user:
        raise LookupError("No user with that ID exists.")
    if not user.ban:
        raise BanError("User is not banned.")

    if user.ban.posts_hidden:
        Post.query.filter_by(uploader_id=user.id).update({"hidden": False})

    db.session.delete(user.ban)
    db.session.commit()

    return user
