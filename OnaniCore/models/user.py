# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:03:01
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-22 10:23:14

from datetime import datetime, timedelta

from aenum import Enum, MultiValue
from dateutil import tz
from passlib.hash import argon2

from ..exceptions import OnaniAuthenticationError
from ..utils import setup_logger

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
        "paypal",
        "pixiv",
        "twitter",
    )

    def __init__(
        self,
        deviantart: str = None,
        discord: str = None,
        github: str = None,
        patreon: str = None,
        paypal: str = None,
        pixiv: str = None,
        twitter: str = None,
    ):
        self.deviantart = deviantart
        self.discord = discord
        self.github = github
        self.patreon = patreon
        self.paypal = paypal
        self.pixiv = pixiv
        self.twitter = twitter

    def to_dict(self) -> dict:
        return {x: getattr(self, x) for x in self.__slots__}

    def __repr__(self):
        return self.to_dict()

    def set_value(self, key: str, value: str) -> None:
        if not key in self.__slots__:
            raise KeyError("Key does not exist.")

        setattr(self, key, value)


class UserSettings(object):
    """
    Settings for User objects
    """

    def __init__(self, **kwargs):
        self.__dict__.update(
            {
                "profile_pic": "/image/default.png",
                "bio": None,
                "tag_blacklist": [],
                "platforms": UserPlatforms(),
            }
        )
        self.__dict__.update(kwargs)

    def update(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def to_dict(self) -> dict:
        _dict = dict(self.__dict__)
        _dict["platforms"] = self.platforms.to_dict()
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
        "api_key",
        "created_at",
        "email",
        "favourites",
        "id",
        "permissions",
        "settings",
        "username",
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
        self._db.modify_user(self, email=new_email)

    def edit_password(self, old_password: str, new_password: str):
        if not self.try_auth(old_password):
            raise OnaniAuthenticationError("Incorrect Password.")
        self._db.modify_user(self, password=new_password)

    def edit_permissions(self, new_permissions: UserPermissions) -> None:
        self._db.modify_user(self, permissions=new_permissions)

    def edit_settings(self, **kwargs) -> None:
        self._db.modify_user(self, settings=kwargs)

    def regen_api_key(self) -> None:
        self._db.regen_user_api_key(self)

    def add_favourite(self, post) -> None:
        self._db.add_user_favourite(self, post)

    def remove_favourite(self, post) -> None:
        self._db.remove_user_favourite(self, post)

    def try_auth(self, password: str):
        if password is None:
            return False
        auth = argon2.verify(password, self._pass_hash)
        return auth

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

    def has_permissions(self, permissions: UserPermissions) -> bool:
        return (
            self.permissions >= permissions
            if permissions != UserPermissions.BANNED
            else False
        )

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
