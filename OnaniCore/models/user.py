# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:03:01
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-16 00:33:54

import logging
from datetime import datetime, timedelta

from aenum import Enum, MultiValue
from dateutil import tz
from flask_login import UserMixin
from passlib.hash import argon2

from ..utils import setup_logger

log = setup_logger(__name__)


class UserSettings(object):
    """
    Settings for User objects
    """

    def __init__(self, **kwargs):
        self.__dict__.update(
            {"profile_pic": "/image/default.png", "bio": None, "tag_blacklist": []}
        )
        self.__dict__.update(kwargs)

    def update(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def to_dict(self) -> dict:
        return self.__dict__

    def __repr__(self):
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
        "_ban",
        "_db",
        "_is_active",
        "_is_authenticated",
        "_pass_hash",
        "api_key",
        "created_at",
        "email",
        "favourites",
        "id",
        "permissions",
        "settings",
        "username",
        "connected_to",
    )

    def __init__(
        self,
        db,
        id: int,
        username: str,
        email: str,
        permissions: UserPermissions,
        favourites: list,
        settings: UserSettings,
        api_key: str,
        created_at: datetime,
        is_active: bool,
        pass_hash: str,
    ):
        self._ban = None
        self._db = db
        self._is_active = is_active
        self._is_authenticated = False
        self._pass_hash = pass_hash
        self.api_key = api_key
        self.created_at = created_at.replace(tzinfo=tz.tzutc())
        self.email = email
        self.favourites = favourites
        self.id = id
        self.permissions = permissions
        self.settings = settings
        self.username = username

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

    def edit_email(self, new_email: str) -> None:
        # TODO #29 edit email
        raise NotImplementedError

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
            self._is_authenticated = True
        return auth

    def deauthenticate(self) -> None:
        if self.is_authenticated:
            self._is_authenticated = False

    def get_ban(self):
        if self.is_banned:
            if self._ban is None:
                self._ban = self._db.get_user_ban(self)
        else:
            self._ban = None
        return self._ban

    @property
    def is_banned(self):
        return self.permissions == UserPermissions.BANNED

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def __eq__(self, other):
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', permissions='{self.permissions}', created_at='{self.created_at}')>"
