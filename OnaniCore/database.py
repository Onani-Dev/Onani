# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-13 18:26:51

import logging
from datetime import datetime

import pymongo

from .models import *

log = logging.getLogger(__name__)


class DatabaseController:
    def __init__(
        self, client: pymongo.MongoClient,
    ):
        # our database and collections for convenience
        self.client = client
        self.db = self.client["OnaniDB"]
        self.posts = self.db["OnaniPosts"]
        self.tags = self.db["OnaniTags"]
        self.users = self.db["OnaniUsers"]
        self.collections = self.db["OnaniCollections"]

    def add_post(self, data: [list, dict]):
        # add a post (or multiple) to the database
        if isinstance(data, list):
            self.posts.insert_many(data)
        else:
            x = self.posts.insert_one(data)
            print(x.inserted_id)

    def add_user(self, data: [list, dict]):
        pass

    def add_collection(self, data: [list, dict]):
        pass

    def add_tag(self, data: [list, dict]):
        pass

    def get_raw_tag_info(self, tag_string: str) -> dict:
        # return raw tag data from database
        return dict()

    def _parse_tags(self, tags: list) -> list:
        tgs = set()
        for tag in tags:
            tgs.add(tag.strip().replace(" ", "_").lower())
        return list(tgs)
