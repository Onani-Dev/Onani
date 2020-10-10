# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-11 02:24:25

from datetime import datetime
from typing import List

from aenum import Enum, MultiValue
from dateutil import tz

from ..utils import setup_logger
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
        file: File,
        tags: List[Tag],
        uploaded_at: datetime = datetime.utcnow(),
        source: str = None,
        rating: PostRating = PostRating.YELLOW,
        status: PostStatus = PostStatus.PENDING,
        uploader: User = None,
        score: dict = {"likers": [], "dislikers": []},
        favourites: list = list(),
        commentary: Commentary = None,
        notes: List[Note] = list(),
    ):
        self._db = db
        self._commentary = commentary
        self._favourites = favourites
        self._file = file
        self._id = id
        self._notes = notes
        self._rating = rating
        self._score = score
        self._source = source
        self._status = status
        self._tags = tags
        self._uploaded_at = uploaded_at.replace(tzinfo=tz.tzutc())
        self._uploader = uploader

    @property
    def commentary(self) -> Commentary:
        return self._commentary

    @commentary.setter
    def commentary(self, value: Commentary) -> None:
        if not isinstance(value, Commentary):
            raise TypeError("Type must be 'Commentary'")

        # update post in database
        self._db.posts.update_one({"_id": self.id}, {"$set": {"commentary": value}})

        # Log
        log.info(
            f"Post {self.id}: Commentary Updated from '{self.commentary}' to '{value}'."
        )

        # update local
        self._commentary = value

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

    @rating.setter
    def rating(self, value: PostRating) -> None:
        if not isinstance(value, PostRating):
            raise TypeError("Type must be 'PostRating'")

        # update post in database
        self._db.posts.update_one({"_id": self.id}, {"$set": {"rating": value.value}})

        # Log
        log.info(
            f"""Post {self.id}: Rating Updated from '{self.rating}' to '{value}'."""
        )

        # Update the local
        self._score = value

    @property
    def score(self) -> dict:
        return self._score

    @property
    def int_score(self) -> int:
        return len(self.score["likers"]) - len(self.score["dislikers"])

    @score.setter
    def score(self, value: dict) -> None:
        if not isinstance(value, dict):
            raise TypeError("Type must be 'dict'")

        # update post in database
        self._db.posts.update_one({"_id": self.id}, {"$set": {"score": value}})

        # Log
        log.info(
            f"""Post {self.id}: Score Updated from '{self.int_score}' to '{len(value["likers"]) - len(value["dislikers"])}'."""
        )

        # Update the local
        self._score = value

    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Type must be 'str'")

        # update post in database
        self._db.posts.update_one({"_id": self.id}, {"$set": {"source": value}})

        # Log
        log.info(
            f"""Post {self.id}: Source Updated from '{self.source}' to '{value}'."""
        )

        # Update the local
        self._source = value

    @property
    def status(self) -> PostStatus:
        return self._status

    @status.setter
    def status(self, value: PostStatus) -> None:
        if not isinstance(value, PostStatus):
            raise TypeError("Type must be 'PostStatus'")

        # update post in database
        self._db.posts.update_one({"_id": self.id}, {"$set": {"status": value.value}})

        # Log
        log.info(
            f"""Post {self.id}: Status Updated from '{self.status}' to '{value}'."""
        )

        # Update the local
        self._status = value

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

    # SCORE METHODS
    def increase_score(self, user: User) -> None:
        # Check if user has liked or disliked it
        if user.id in self.score["likers"]:
            # user had liked this post
            raise ValueError("User has already liked this Post.")

        if user.id in self.score["dislikers"]:
            # user had disliked this post
            self.score["dislikers"].remove(self.id)

        # Append to likers
        self.score["likers"].append(self.id)

        # log
        log.info(f"Post {self.id}: {user.username} ({user.id}) Liked post.")

    def decrease_score(self, user: User) -> None:
        # Check if user has liked or disliked it
        if user.id in self.score["likers"]:
            # user had liked this post
            self.score["likers"].remove(self.id)

        if user.id in self.score["dislikers"]:
            # user had disliked this post
            raise ValueError("User has already disliked this Post.")

        # Append to dislikers
        self.score["dislikers"].append(self.id)

        # log
        log.info(f"Post {self.id}: {user.username} ({user.id}) Disliked post.")

    def remove_score(self, user: User) -> None:
        # Check if user has liked or disliked it
        if user.id in self.score["likers"]:
            # user had liked this post
            self.score["likers"].remove(self.id)

        if user.id in self.score["dislikers"]:
            # user had disliked this post
            self.score["dislikers"].remove(self.id)

        # log
        log.info(f"Post {self.id}: {user.username} ({user.id}) Removed score on post.")

    def to_dict(self) -> dict:
        return {
            "commentary": self.commentary.to_dict(),
            "favourites": self.favourites,
            "id": self.id,
            "notes": [note.to_dict() for note in self.notes],
            "rating": self.rating.value,
            "score": self.score,
            "source": self.source,
            "status": self.status.value,
            "uploaded_at": self.uploaded_at,
            "uploader": self.uploader.id,
            "file": self.file.to_dict(),
            "tags": [tag.id for tag in self.tags],
        }

    def __repr__(self):
        return f"<Post(id={self.id}, file='{self.file}' status='{self.status}', uploader='{self.uploader}')>"
