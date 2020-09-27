# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-27 13:55:47

from json import dumps

from aenum import Enum, MultiValue

from ..utils import setup_logger

log = setup_logger(__name__)


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

    __slots__ = (
        "_db",
        "id",
        "aliases",
        "description",
        "popularity",
        "post_count",
        "string",
        "type",
    )

    def __init__(
        self,
        db,
        id: int,
        tag_string: str,
        tag_type: TagType,
        aliases: list = list(),
        description: str = None,
        post_count: int = 0,
        popularity: float = 0.0,
    ):
        self._db = db
        self.id = id
        self.string = tag_string
        self.type = tag_type
        self.aliases = aliases
        self.description = description
        self.post_count = post_count
        self.popularity = popularity

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

    def modify_post_count(self, amount: int = 1) -> None:
        self._db.modify_tag(self, post_count=amount)

    def modify_popularity(self, amount: float = 0.001) -> None:
        self._db.modify_tag(self, popularity=amount)

    def __str__(self):
        return self.string

    def __repr__(self):
        return f"<Tag(string='{self.string}', type='{self.type}', aliases='{dumps(self.aliases)}')>"
