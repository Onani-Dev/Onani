# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-05 19:37:18

from datetime import datetime
from typing import List

from aenum import Enum, MultiValue
from dateutil import tz

from ..utils import html_escape, setup_logger
from .commentary import Commentary
from .file import File
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

    def __init__(
        self, db,
    ):
        self._db = db

    # UPLOADED AT
    @property
    def uploaded_at(self) -> datetime:
        return self._uploaded_at

    @uploaded_at.setter
    def uploaded_at(self, value: datetime) -> datetime:
        # database stuff blah blah
        self._uploaded_at = value.replace(tzinfo=tz.tzutc())
        return self._uploaded_at

    # SOURCE
    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str) -> str:
        # database stuff blah blah
        self._source = html_escape(value)

    # RATING
    @property
    def rating(self) -> int:
        return self._rating

    @rating.setter
    def rating(self, value: PostRating) -> None:
        # DATAAAAAAAAAAAAAAAAAAAAAAAAAA
        self._rating = value

    # STATUS
    @property
    def status(self) -> PostStatus:
        return self._status

    @status.setter
    def status(self, value: PostStatus):
        # Database shit
        self._status = value

    # UPLOADER
    @property
    def uploader(self) -> User:
        return self._uploader

    @uploader.setter
    def uploader(self, value: User) -> None:
        # :pensive:
        self._uploader = value

    # SCORE
    @property
    def score(self) -> int:
        return self._score

    @score.setter
    def score(self, value: int):
        self._score = value

    # FAVOURITES
    @property
    def favourites(self) -> int:
        return self._favourites

    @favourites.setter
    def favourites(self, value: int) -> None:
        self._favourites = value

    # Commentary
    @property
    def commentary(self) -> Commentary:
        return self._commentary

    @commentary.setter
    def commentary(self, value: Commentary) -> None:
        self._commentary = value

    # NOTES
    @property
    def notes(self) -> Note:
        return self._notes

    @notes.setter
    def notes(self, value: Note) -> None:
        self._notes = value

    def to_dict(self) -> dict:
        d = dict()
        for x in [p for p in dir(self) if isinstance(getattr(self, p), property)]:
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
        return f"<PostData(status='{self.status}', uploader='{self.uploader}')>"


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = (
        "_db",
        "_id",
        "_file",
        "_tags",
        "_uploaded_at",
        "_source",
        "_rating",
        "_status",
        "_uploader",
        "_score",
        "_favourites",
        "_commentary",
        "_notes",
    )

    def __init__(
        self,
        db,
        id: int,
        file: dict,
        tags: list,
        uploaded_at: datetime = datetime.utcnow(),
        source: str = None,
        rating: PostRating = PostRating.YELLOW,
        status: PostStatus = PostStatus.PENDING,
        uploader: User = None,
        score: dict = {"likers": [], "dislikers": []},
        favourites: int = 0,
        commentary: Commentary = None,
        notes: List[Note] = list(),
    ):
        self._db = db
        self._commentary = commentary
        self._favourites = favourites
        self._id = id
        self._notes = notes
        self._rating = rating
        self._score = score
        self._source = source
        self._status = status
        self._uploaded_at = uploaded_at.replace(tzinfo=tz.tzutc())
        self._uploader = uploader
        self._file = File(
            filename=file.get("filename"),
            directory=file.get("directory"),
            thumbnail=file.get("thumbnail"),
            hash=file.get("hash"),
            width=file.get("width"),
            height=file.get("height"),
            filesize=file.get("filesize"),
        )
        self._tags = [
            Tag(
                db=self._db,
                tag_string=x.get("string"),
                tag_type=TagType(x.get("type", 1)),
                aliases=x.get("aliases", list()),
                description=x.get("description"),
                post_count=x.get("post_count", 0),
                popularity=x.get("popularity", 0.0),
            )
            for x in tags
        ]

    @property
    def commentary(self) -> Commentary:
        return self._commentary

    @property
    def favourites(self) -> list:
        return self._favourites

    @property
    def id(self) -> int:
        return self._id

    @property
    def notes(self) -> List[Note]:
        return self._notes

    @property
    def rating(self) -> PostRating:
        return self._rating

    @property
    def score(self) -> dict:
        return self._score

    @property
    def source(self) -> str:
        return self._source

    @property
    def status(self) -> PostStatus:
        return self._status

    @property
    def uploaded_at(self) -> datetime:
        return self._uploaded_at

    @property
    def uploader(self) -> User:
        return self._uploader

    @property
    def file(self) -> File:
        return self._file

    @property
    def tags(self) -> List[Tag]:
        return self._tags

    def add_tags(self, tags: List[Tag]):
        pass

    def remove_tags(self, tags: List[Tag]):
        # add stuff for adding tags here
        pass

    def __repr__(self):
        return f"<Post(id={self.id}, file='{self.file}')>"
