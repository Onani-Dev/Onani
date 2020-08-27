# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-22 01:03:56
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-27 22:29:38

import logging
from datetime import datetime
from typing import List

from aenum import Enum, MultiValue

from .post import Post
from .user import User

log = logging.getLogger(__name__)


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
        self.created_at = created_at
        self.creator = creator
        self.rating

    def add_post(self, post: Post, index: int = None):
        if index is not None:
            self.posts.insert(index, post)
        else:
            self.posts.append(post)
