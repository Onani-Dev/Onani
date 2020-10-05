# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:03:01
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-05 22:00:25

import re
from datetime import datetime, timedelta

from aenum import Enum, MultiValue
from dateutil import tz
from passlib.hash import argon2

from ..exceptions import (
    OnaniAuthenticationError,
    OnaniPermissionError,
    OnaniDatabaseException,
)
from ..utils import setup_logger, is_safe_email
from .file import File

log = setup_logger(__name__)


class UserPlatforms(object):
    """
    User Platforms (Socials)
    """

    __slots__ = (
        "deviantart",
        "discord",
        "github",
        "patreon",
        "pixiv",
        "twitter",
    )

    def __init__(
        self,
        deviantart: str = None,
        discord: str = None,
        github: str = None,
        patreon: str = None,
        pixiv: str = None,
        twitter: str = None,
    ):
        self.deviantart = deviantart
        self.discord = discord
        self.github = github
        self.patreon = patreon
        self.pixiv = pixiv
        self.twitter = twitter

    def to_dict(self) -> dict:
        return {x: getattr(self, x) for x in self.__slots__}

    def __repr__(self):
        return self.to_dict()

    def set_values(self, **kwargs) -> None:
        for key in kwargs:
            if not key in self.__slots__:
                raise KeyError("Key does not exist.")
            setattr(self, key, kwargs[key])

    def set_value(self, key: str, value: str) -> None:
        if not key in self.__slots__:
            raise KeyError("Key does not exist.")

        setattr(self, key, value)


class UserSettings(object):
    """
    Settings for User objects
    """

    def __init__(
        self,
        avatar: File = File(),
        bio: str = str(),
        tag_blacklist: list = ["guro", "scat", "furry"],
        platforms: UserPlatforms = UserPlatforms(),
    ):
        self.avatar = avatar
        self.bio = bio
        self.tag_blacklist = tag_blacklist
        self.platforms = platforms

    def update(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def to_dict(self) -> dict:
        _dict = dict(self.__dict__)
        _dict["platforms"] = self.platforms.to_dict()
        _dict["avatar"] = self.avatar.to_dict()
        return _dict

    def __repr__(self):
        return self.to_dict()


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

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value


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
        "_api_key",
        "_created_at",
        "_email",
        "_favourites",
        "_id",
        "_permissions",
        "_settings",
        "_username",
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
        self._pass_hash = pass_hash
        self._api_key = api_key
        self._created_at = created_at.replace(tzinfo=tz.tzutc())
        self._email = email
        self._favourites = favourites
        self._id = id
        self._permissions = permissions
        self._settings = settings
        self._username = username

    # IS ACTIVE (Flask login property)
    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        # Check typing
        if not isinstance(value, bool):
            raise ValueError("Value must be bool.")

        # Set value
        self._db.users.update_one({"_id": self.id}, {"$set": {"is_active": value}})

        # Add to log
        log.info(f"User {self.username} ({self.id}): is_active = {value}")

        # Set the class value
        self._is_active = value

    # PASSWORD HASH
    @property
    def pass_hash(self) -> str:
        return self._pass_hash

    # API KEY
    @property
    def api_key(self) -> str:
        return self._api_key

    # CREATED AT (Readonly)
    @property
    def created_at(self) -> datetime:
        return self._created_at

    # EMAIL
    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        # Check email
        if not is_safe_email(value):
            raise ValueError("Email is invalid.")

        # Check for a user with the same email
        existing_user = self._db.users.find_one({"email": value})

        if existing_user is not None:
            # We can't use this email.
            raise OnaniDatabaseException("Email is in use.")

        # set in db
        self._db.users.update_one({"_id": self.id}, {"$set": {"email": value}})

        # Add to log
        log.info(
            f'User {self.username} ({self.id}): User email changed from "{self.email}" to "{value}"'
        )

        # Set local value
        self._email = value

    # FAVOURITES
    @property
    def favourites(self) -> list:
        return self._favourites

    # ID (Readonly)
    @property
    def id(self) -> int:
        return self._id

    # PERMISSIONS
    @property
    def permissions(self) -> UserPermissions:
        return self._permissions

    @permissions.setter
    def permissions(self, value: UserPermissions) -> None:
        self._db.edit_user(self, permissions=value)

    # SETTINGS
    @property
    def settings(self) -> UserSettings:
        return self._settings

    # USERNAME
    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        # Check if an existing user exists with this username
        existing_user = self._db.users.find_one(
            {"username": re.compile(fr"\b{value}\b", re.IGNORECASE)}
        )

        if existing_user is not None:
            # We can't use this username.
            raise OnaniDatabaseException("Username is taken.")

        # Set current users name to new value
        self._db.users.update_one({"_id": self.id}, {"$set": {"username": value}})

        # Add to log
        log.info(
            f'User {self.username} ({self.id}): User username changed from "{self.username}" to "{value}"'
        )

        # Set the class value
        self._username = value

    # IS AUTHENTICATED (Always True)
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_banned(self):
        return self.permissions == UserPermissions.BANNED

    @property
    def is_anonymous(self):
        return False

    def ban(
        self, reason: str, duration: timedelta = timedelta(days=30), ban_creator=None,
    ) -> None:
        if ban_creator:
            if not ban_creator.has_permissions(UserPermissions.ADMINISTRATOR):
                raise OnaniPermissionError("Insufficient Permissions.")
        self._db.add_user_ban(
            self, reason, duration, (self if ban_creator is None else ban_creator)
        )

    def unban(self) -> None:
        self._db.remove_user_ban(self)

    def change_password(self, old_password: str, new_password: str):
        if not self.try_auth(old_password):
            raise OnaniAuthenticationError("Incorrect Password.")
        self._db.edit_user(self, password=new_password)

    def edit_settings(self, **kwargs) -> None:
        self._db.edit_user(self, settings=kwargs)

    def edit_platforms(self, **kwargs) -> None:
        self._db.edit_user(self, platforms=kwargs)

    def regen_api_key(self) -> None:
        self._db.regen_user_api_key(self)

    def authenticate(self, password: str) -> bool:
        if not password:
            return False
        auth = argon2.verify(password, self._pass_hash)
        return auth

    def get_ban(self):
        if self.is_banned:
            if self._ban is None:
                self._ban = self._db.get_user_ban(self)
        else:
            self._ban = None
        return self._ban

    def has_permissions(self, permissions: UserPermissions) -> bool:
        return (
            self.permissions >= permissions
            if permissions != UserPermissions.BANNED
            else False
        )

    def get_id(self):  # Flask login thing
        return self.id

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
