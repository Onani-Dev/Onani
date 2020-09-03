# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-03 19:20:21

import logging
from datetime import datetime
from typing import List

from aenum import Enum, MultiValue

from ..utils import setup_logger
from .commentary import Commentary
from .note import Note
from .tag import Tag, TagType
from .user import User

log = setup_logger(__name__)


class PostRating(Enum):
    """
    Ratings for Post objects
    """

    _init_ = "value string"
    _settings_ = MultiValue

    GREEN = 1, "Green"
    YELLOW = 2, "Yellow"
    RED = 3, "Red"

    def __int__(self):
        return self.value


class PostStatus(Enum):
    """
    Status for Post objects
    """

    _init_ = "value string"
    _settings_ = MultiValue

    DELETED = 0, "Deleted"
    PENDING = 1, "Pending"
    ACCEPTED = 2, "Accepted"

    def __int__(self):
        return self.value


class PostFile(object):
    """
    Post File object (May need to change slightly for AWS S3)
    """

    __slots__ = ("filename", "directory", "thumbnail")

    def __init__(
        self, filename: str = None, directory: str = None, thumbnail: str = None
    ):
        self.filename = filename
        self.directory = directory
        self.thumbnail = thumbnail

    def to_dict(self) -> dict:
        return {x: getattr(self, x) for x in self.__slots__}

    def __repr__(self):
        return f"<PostFile(directory='{self.directory}', filename='{self.filename}')>"


class PostData(object):
    """
    Data for Post objects
    """

    __slots__ = (
        "_db",
        "md5",
        "uploaded_at",
        "source",
        "rating",
        "status",
        "uploader",
        "height",
        "width",
        "filesize",
        "score",
        "favourites",
        "commentary",
        "notes",
    )

    def __init__(
        self,
        db,
        md5: str = None,
        uploaded_at: datetime = datetime.utcnow(),
        source: str = None,
        rating: PostRating = PostRating.YELLOW,
        status: PostStatus = PostStatus.PENDING,
        uploader: User = None,
        height: int = 0,
        width: int = 0,
        filesize: int = 0,
        score: int = 0,
        favourites: int = 0,
        commentary: Commentary = None,
        notes: List[Note] = list(),
    ):
        self._db = db
        self.md5 = md5
        self.uploaded_at = uploaded_at
        self.source = source
        self.rating = rating
        self.status = status
        self.uploader = uploader
        self.height = height
        self.width = width
        self.filesize = filesize
        self.score = score
        self.favourites = favourites
        self.commentary = commentary
        self.notes = notes

    def to_dict(self) -> dict:
        d = dict()
        for x in self.__slots__:
            if isinstance(getattr(self, x), (User, Commentary, Note)):
                # object is able to be turned into a dict
                d[x] = getattr(self, x).to_dict()
            elif isinstance(getattr(self, x), (PostRating, PostStatus)):
                # object is able to be turned into an int
                d[x] = getattr(self, x).value
            elif x != "_db":
                # object is fine in raw form
                d[x] = getattr(self, x)
        return d

    def __repr__(self):
        return f"<PostData(md5='{self.md5}', uploader='{self.uploader}')>"


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = ("_db", "id", "file", "tags", "data")

    def __init__(self, db, post_id: int, file_data: dict, tags: list, data: dict):
        self._db = db
        self.id = post_id
        self.file = PostFile(
            file_data.get("filename"),
            file_data.get("directory"),
            file_data.get("thumbnail"),
        )
        self.data = PostData(self._db, **data)
        self.tags = [
            Tag(
                self._db,
                x.get("string"),
                TagType(x.get("type")),
                x.get("aliases"),
                x.get("description"),
            )
            for x in tags
        ]

    def add_tags(self, tags: List[Tag]):
        pass

    def remove_tags(self, tags: List[Tag]):
        # add stuff for adding tags here
        pass

    def __repr__(self):
        return f"<Post(id={self.id}, file='{self.file}')>"
