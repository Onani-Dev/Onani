# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-14 00:54:22
import logging

log = logging.getLogger(__name__)


class Tag:
    """
    Onani Tag Object
    """

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


class Post:
    """
    Onani Post Object
    """

    def __init__(self, db, post_data: dict):
        self._db = db
        self.file_url = post_data.get("file_url")
        self.thumb_url = post_data.get("thumb_url")
        self.tags = [Tag(self._db, x) for x in (post_data.get("tags") or list())]
        self.meta = post_data.get("meta")

    def add_tags(self, tags: list):
        pass
