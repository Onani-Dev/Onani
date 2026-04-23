# -*- coding: utf-8 -*-
from onani.models import User, UserRoles

from onani import db


def create_user(
    username: str,
    password: str,
    email: str = None,
    role: UserRoles = UserRoles.MEMBER,
) -> User:
    """Create and persist a new user account."""
    user = User(username=username, email=email, role=role)
    user.set_password(password)
    user.save_to_db()
    return user
