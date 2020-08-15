# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-15 18:30:06
import logging
from datetime import datetime

log = logging.getLogger(__name__)


class Tag(object):
    """
    Onani Tag Object
    """

    __slots__ = (
        "_db",
        "tag_string",
        "raw",
        "type",
        "is_banned",
        "aliases",
        "description",
    )

    def __init__(self, db, tag_string: str):
        self._db = db
        self.tag_string = tag_string
        self.raw = self._db.get_raw_tag_info(self.tag_string)
        self.type = self.raw.get("type") or "Unknown"
        self.is_banned = self.raw.get("is_banned") or False
        self.aliases = self.raw.get("aliases") or list()
        self.description = self.raw.get("description") or str()

    def ban(self):
        self.is_banned = True
        # need to do extra db stuff here

    def edit_description(self, description: str):
        self.description = description
        # need to do extra db stuff here

    def edit_alias(self, mode: str = "add", alias: str = None):
        if alias is None:
            raise ValueError("Alias is missing.")
        if mode == "add":
            self.aliases.append(alias)
        elif mode == "remove":
            self.aliases.remove(alias)
        # need to do extra db stuff here

    def __str__(self):
        return self.tag_string


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = ("_db", "id", "file_url", "thumb_url", "tags", "meta")

    def __init__(self, db, post_data: dict):
        self._db = db
        self.id = int(post_data.get("id"))
        self.file_url = post_data.get("file_url")
        self.thumb_url = post_data.get("thumb_url")
        self.tags = [Tag(self._db, x) for x in (post_data.get("tags") or list())]
        self.meta = post_data.get("meta")

    def add_tags(self, tags: list):
        # add stuff for adding tags here
        pass

    def remove_tags(self, tags: list):
        # add stuff for adding tags here
        pass


class User(object):
    """
    Onani User Object
    """

    __slots__ = (
        "_db",
        "api_key",
        "created_at",
        "favourites",
        "id",
        "permissions",
        "is_banned",
        "settings",
        "username",
    )

    def __init__(
        self,
        db,
        id: int,
        username: str,
        permissions: int,
        is_banned: bool,
        favourites: list,
        settings: dict,
        api_key: str,
        created_at: datetime,
    ):
        self._db = db
        self.api_key = api_key
        self.created_at = created_at
        self.favourites = favourites
        self.id = id
        self.permissions = permissions
        self.is_banned = is_banned
        self.settings = settings
        self.username = username

    def ban(self, reason: str):
        # add ban function for users
        pass

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', created_at='{self.created_at}')>"
