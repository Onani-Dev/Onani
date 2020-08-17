# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-17 20:07:56

import logging
from datetime import datetime

log = logging.getLogger(__name__)


class Post(object):
    """
    Onani Post Object
    """

    __slots__ = ("_db", "id", "file_url", "thumb_url", "tags", "meta")

    def __init__(self, db, post_data: dict):
        self._db = db
        self.id = int(post_data.get("id"))
        self.filename = post_data.get("filename")
        self.thumb_filename = post_data.get("thumb_url")
        self.tags = [Tag(self._db, x) for x in (post_data.get("tags") or list())]
        self.meta = post_data.get("meta")

    def add_tags(self, tags: list):
        # add stuff for adding tags here
        pass

    def remove_tags(self, tags: list):
        # add stuff for adding tags here
        pass
