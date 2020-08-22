# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-22 14:32:34

import logging
from datetime import datetime
from typing import List

from aenum import Enum, MultiValue

from .commentary import Commentary
from .note import Note
from .tag import Tag
from .user import User

log = logging.getLogger(__name__)


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
        uploaded_at: datetime = None,
        source: str = None,
        rating: PostRating = PostRating.YELLOW,
        status: PostStatus = PostStatus.PENDING,
        uploader: User = None,
        height: int = None,
        width: int = None,
        filesize: int = None,
        score: int = None,
        favourites: int = None,
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

    def to_dict(self):
        return {
            x: (
                getattr(self, x).to_dict()
                if isinstance(
                    getattr(self, x), (PostRating, PostStatus, User, Commentary, Note,),
                )
                else getattr(self, x)
            )
            for x in self.__slots__
            if x != "_db"
        }


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = ("_db", "id", "file", "tags", "data")

    def __init__(self, db, post_id: int, file_data: dict, tags: list, data: PostData):
        self._db = db
        self.id = post_id
        self.file = PostFile(**file_data)
        self.tags = [Tag(self._db, x) for x in tags]
        self.data = data

    def add_tags(self, tags: list):
        # add stuff for adding tags here
        pass

    def remove_tags(self, tags: list):
        # add stuff for adding tags here
        pass
