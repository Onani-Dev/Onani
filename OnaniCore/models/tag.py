# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-28 21:33:15

import logging
from json import dumps

from aenum import Enum, MultiValue

log = logging.getLogger(__name__)


class TagType(Enum):
    """
    Types for Tag Objects
    Can be: ARTIST, CHARACTER, COPYRIGHT, GENERAL, META
    """

    _init_ = "value string"
    _settings_ = MultiValue

    BANNED = 0, "Banned"
    GENERAL = 1, "General"
    ARTIST = 2, "Artist"
    CHARACTER = 3, "Character"
    COPYRIGHT = 4, "Copyright"
    META = 5, "Meta"

    def __int__(self):
        return self.value


class Tag(object):
    """
    Onani Tag Object
    """

    __slots__ = ("_db", "string", "type", "aliases", "description", "count")

    def __init__(
        self,
        db,
        tag_string: str,
        tag_type: TagType,
        aliases: list = list(),
        description: str = None,
        count: int = 0,
    ):
        self._db = db
        self.string = tag_string
        self.type = tag_type
        self.aliases = aliases
        self.description = description
        self.count = count

    def edit_name(self, new_name: str) -> None:
        self._db.modify_tag(self, tag_string=new_name)

    def edit_type(self, new_type: TagType) -> None:
        self._db.modify_tag(self, tag_type=new_type)

    def ban(self) -> None:
        self._db.modify_tag(self, tag_type=TagType.BANNED)

    def unban(self, tag_type: TagType = TagType.GENERAL) -> None:
        self._db.modify_tag(self, tag_type=tag_type)

    def edit_description(self, description: str) -> None:
        self._db.modify_tag(self, description=description)

    def add_alias(self, alias: str) -> None:
        self._db.add_tag_alias(self, alias)

    def remove_alias(self, alias: str) -> None:
        self._db.remove_tag_alias(self, alias)

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"<Tag(string='{self.string}', type='{self.type}', aliases='{dumps(self.aliases)}')>"
