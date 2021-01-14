# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-11-01 18:18:30

from collections import Iterable
from json import dumps
from typing import Union

from aenum import Enum, MultiValue

from ..utils import *

log = setup_logger(__name__)


class AliasList(list):
    """
    Subclassed list object for tag aliases
    """

    def __init__(self, *args):
        list.__init__(self, parse_tags(list(args)))

    def append(self, value) -> None:
        list.append(self, parse_tag(value))

    def extend(self, values: Iterable) -> None:
        list.extend(self, parse_tags(values))


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
        "_aliases",
        "_db",
        "_description",
        "_id",
        "_name",
        "_popularity",
        "_post_count",
        "_type",
    )

    def __init__(
        self,
        db,
        id: int,
        tag_string: str,
        tag_type: TagType,
        aliases: AliasList = AliasList(),
        description: str = None,
        post_count: int = 0,
        popularity: float = 0.0,
    ):
        self._db = db
        self._id = id
        self._name = tag_string
        self._type = tag_type
        self._aliases = aliases
        self._description = description
        self._post_count = post_count
        self._popularity = popularity

    # ID (Readonly)
    @property
    def id(self) -> int:
        return self._id

    # NAME
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        # Check the type
        if not isinstance(value, str):
            # Wrong type!
            raise TypeError("Wrong object type for name.")

        # Parse the string
        tag_string = parse_tag(value)

        # Update document in mongodb
        self._db.tags.update_one(
            {"_id": self.id}, {"$set": {"string": tag_string}},
        )

        # Log to db
        log.info(f'Tag {self.name}: name changed to "{tag_string}"')

        # Set class name to updated name
        self._name = tag_string

    # TYPE
    @property
    def type(self) -> TagType:
        return self._type

    @type.setter
    def type(self, value: TagType) -> None:
        # Check type
        if not isinstance(value, TagType):
            # Wrong
            raise TypeError("Wrong object type for type.")

        # Update mongo doc
        self._db.tags.update_one(
            {"_id": self.id}, {"$set": {"type": value.value}},
        )

        # Log
        log.info(f'Tag {self.name}: Type changed from "{self.type}" to "{value}"')

        # Update class value
        self._type = value

    # ALIASES
    @property
    def aliases(self) -> list:
        return self._aliases

    # DESCRIPTION
    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        # Check the type
        if not isinstance(value, str):
            # Wrong type!
            raise TypeError("Wrong object type for description.")

        # Update document in mongodb
        self._db.tags.update_one(
            {"_id": self.id}, {"$set": {"description": value}},
        )

        # Log
        log.info(
            f'Tag {self.name}: Description changed from "{self.description}" to "{value}"'
        )

        # Update
        self._description = value

    # POST COUNT
    @property
    def post_count(self) -> int:
        return self._post_count

    @post_count.setter
    def post_count(self, value: int) -> None:
        # Check the type
        if not isinstance(value, int):
            # not int >:(
            raise TypeError("Wrong object type for post_count.")

        # Update doc
        self._db.tags.update_one(
            {"_id": self.id}, {"$set": {"post_count": value}},
        )

        # Log shit
        log.info(
            f'Tag {self.name}: Post Count changed from "{self.post_count}" to "{value}"'
        )

        # Update local
        self._post_count = value

    # POPULARITY
    @property
    def popularity(self) -> float:
        return self._popularity

    @popularity.setter
    def popularity(self, value: Union[int, float]) -> None:
        # Check the type
        if not isinstance(value, (int, float)):
            # not int or float
            raise TypeError("Wrong object type for description.")

        # Update
        self._db.tags.update_one(
            {"_id": self.id}, {"$set": {"popularity": value}},
        )

        # Log shit
        log.info(
            f'Tag {self.name}: Post Popularity changed from "{self.popularity}" to "{value}"'
        )

        # set local
        self._popularity = value

    # FUNCTIONS
    def ban(self) -> None:
        self.type = TagType.BANNED

    def unban(self, tag_type: TagType = TagType.GENERAL) -> None:
        self.type = tag_type

    def add_alias(self, alias: str) -> None:
        alias = parse_tag(alias)
        update = self._db.tags.update_one(
            {"_id": self.id}, {"$addToSet": {"aliases": alias}}
        )
        if update.modified_count > 0:
            self._aliases.append(alias)
            log.debug(f'Alias added for tag "{self.name}"')
        else:
            log.debug("Alias was not added as it already exists.")

    def remove_alias(self, alias: str) -> None:
        update = self._db.tags.update_one(
            {"_id": self.id}, {"$pull": {"aliases": alias}}
        )
        if update.modified_count > 0:
            self._aliases.remove(alias)
            log.debug(f'Alias removed for tag "{self.name}"')
        else:
            log.debug("Alias was not removed as it doesnt't exist.")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Tag(name='{self.name}', type='{self.type}', aliases='{dumps(self.aliases)}')>"

    def __eq__(self, other):
        return self.name == other.name or other.name in self.aliases
