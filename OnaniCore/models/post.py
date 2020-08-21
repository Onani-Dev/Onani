# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-21 23:56:58

import logging
from datetime import datetime

from ..models.tag import Tag, TagType

log = logging.getLogger(__name__)


class PostFile(object):
    """
    Post File object (May need to change slightly for AWS S3)
    """

    __slots__ = ("filename", "directory", "thumbnail")

    def __init__(self, filename: str, directory: str, thumbnail: str):
        self.filename = filename
        self.directory = directory
        self.thumbnail = thumbnail


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = ("_db", "id", "file", "tags", "meta")

    def __init__(self, db, post_data: dict):
        self._db = db
        self.id = int(post_data.get("id"))
        self.filename = post_data.get("filename")
        self.thumbname = post_data.get("thumb_url")
        self.tags = [Tag(self._db, x) for x in (post_data.get("tags") or list())]
        self.meta = post_data.get("meta")

    def add_tags(self, tags: list):
        # add stuff for adding tags here
        pass

    def remove_tags(self, tags: list):
        # add stuff for adding tags here
        pass
