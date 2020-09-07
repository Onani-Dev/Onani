# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:03:01
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-07 14:20:14

import logging
from datetime import datetime, timedelta

from aenum import Enum, MultiValue
from passlib.hash import argon2

from ..utils import setup_logger

log = setup_logger(__name__)


class UserSettings(object):
    """
    Settings for User objects
    """

    def __init__(self, **kwargs):
        self.__dict__.update({"profile_pic": "/image/default.png", "bio": None})
        self.__dict__.update(kwargs)

    def update(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def to_dict(self) -> dict:
        return self.__dict__


class UserPermissions(Enum):
    """
    Permissions for User objects.
    """

    _init_ = "value string"
    _settings_ = MultiValue

    BANNED = 0, "Banned"
    MEMBER = 1, "Member"
    ARTIST = 2, "Artist"
    PREMIUM = 3, "Premium"
    HELPER = 4, "Helper"
    MODERATOR = 5, "Moderator"
    ADMINISTRATOR = 6, "Administrator"
    OWNER = 666, "Owner"

    def __int__(self):
        return self.value


class User(object):
    """
    Onani User Object
    """

    __slots__ = (
        "_db",
        "_pass_hash",
        "api_key",
        "created_at",
        "favourites",
        "id",
        "is_active",
        "permissions",
        "settings",
        "username",
        "is_authenticated",
        "is_anonymous",
    )

    def __init__(
        self,
        db,
        id: int,
        username: str,
        permissions: UserPermissions,
        favourites: list,
        settings: UserSettings,
        api_key: str,
        created_at: datetime,
        is_active: bool,
        pass_hash: str,
    ):
        self._db = db
        self.api_key = api_key
        self.created_at = created_at
        self.favourites = favourites
        self.id = id
        self.permissions = permissions
        self.settings = settings
        self.username = username
        self.is_active = is_active
        self._pass_hash = pass_hash

        # Flask login

        self.is_authenticated = False
        self.is_anonymous = False

    def ban(
        self, reason: str, duration: timedelta = timedelta(days=30), ban_creator=None,
    ) -> None:
        self._db.add_user_ban(
            self, reason, duration, (self if ban_creator is None else ban_creator)
        )

    def unban(self) -> None:
        self._db.remove_user_ban(self)

    def edit_username(self, new_username: str) -> None:
        self._db.modify_user(self, username=new_username)

    def add_favourite(self, post) -> None:
        self._db.add_user_favourite(self, post)

    def remove_favourite(self, post) -> None:
        self._db.remove_user_favourite(self, post)

    def edit_permissions(self, new_permissions: UserPermissions) -> None:
        self._db.modify_user(self, permissions=new_permissions)

    def edit_settings(self, **kwargs) -> None:
        self._db.modify_user(self, settings=kwargs)

    def regen_api_key(self) -> None:
        self._db.regen_user_api_key(self)

    def authenticate(self, password: str) -> bool:
        auth = argon2.verify(password, self._pass_hash)
        if auth:
            self.is_authenticated = True
        return auth

    def __repr__(self) -> None:
        return f"<User(id={self.id}, username='{self.username}', permissions='{self.permissions}', created_at='{self.created_at}')>"

    ## Flask login

    def get_id(self):
        return self.username
