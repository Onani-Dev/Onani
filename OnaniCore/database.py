# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-12 21:24:16

import logging
import pymongo


log = logging.getLogger(__name__)


class DatabaseController:
    def __init__(
        self,
        client: pymongo.MongoClient = pymongo.MongoClient("mongodb://localhost:27017/"),
    ):
        self.client = client
        self.db = self.client["OnaniDB"]
        self.posts = self.db["OnaniPosts"]
        self.tags = self.db["OnaniTags"]
        self.collections = self.db["OnaniCollections"]
        self.users = self.db["OnaniUsers"]

    def test(self, data):
        x = self.posts.insert_one(data)
        print(x.inserted_id)
