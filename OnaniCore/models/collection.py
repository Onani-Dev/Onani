# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-22 01:03:56
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-27 12:38:40

from datetime import datetime
from typing import List

from aenum import Enum, MultiValue
from dateutil import tz

from ..utils import setup_logger
from .post import Post
from .user import User

log = setup_logger(__name__)


class CollectionStatus(Enum):
    """
    Status for collections
    """

    _init_ = "value string"
    _settings_ = MultiValue

    BANNED = 0, "Banned"
    PENDING = 1, "Pending"
    ACCEPTED = 2, "Accepted"

    def __int__(self):
        return self.value


class Collection(object):

    __slots__ = (
        "_db",
        "id",
        "title",
        "description",
        "posts",
        "status",
        "created_at",
        "creator",
        "rating",
    )

    def __init__(
        self,
        db,
        id: int,
        title: str,
        description: str,
        posts: List[Post],
        status: CollectionStatus,
        created_at: datetime,
        creator: User,
        rating: int,
    ):
        self._db = db
        self.id = id
        self.title = title
        self.description = description
        self.posts = posts
        self.status = status
        self.created_at = created_at.replace(tzinfo=tz.tzutc())
        self.creator = creator
        self.rating = rating

    def add_post(self, post: Post, index: int = None):
        if index is not None:
            self.posts.insert(index, post)
        else:
            self.posts.append(post)
