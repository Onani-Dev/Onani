# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-15 23:11:55

import logging
import os
import random
import re
import string
from binascii import hexlify
from datetime import datetime

import pymongo
from werkzeug.security import generate_password_hash

from .models import *
from .permissions import UserPermissions

log = logging.getLogger(__name__)


class DatabaseController:
    """
    Controller for the Onani Database
    """

    __slots__ = ("client", "db", "posts", "tags", "users", "collections", "bans")

    def __init__(
        self, client: pymongo.MongoClient,
    ):
        self.client = client
        self.db = self.client["OnaniDB"]
        self.bans = self.db["OnaniBans"]
        self.collections = self.db["OnaniCollections"]
        self.posts = self.db["OnaniPosts"]
        self.tags = self.db["OnaniTags"]
        self.users = self.db["OnaniUsers"]

    ## ADDING

    def add_post(self, **kwargs) -> None:
        # add a post to the database
        x = self.posts.insert_one(data)
        print(x.inserted_id)

    def add_user(self, **kwargs) -> None:
        # add a user to the database
        if kwargs.get("password") is None:
            # We didnt recieve a password
            raise ValueError("Accounts MUST have a password.")

        # Check if Username is already taken, If one is supplied.
        if kwargs.get("username") is not None:
            user = self.users.find_one(
                {"username": re.compile(kwargs.get("username"), re.IGNORECASE)}
            )
            if user is not None:
                # We can't use this username.
                raise ValueError("Username is taken.")
            log.debug(f""""{kwargs.get("username")}" looks good to use.""")

        # Construct dict to insert into database
        user_data = {
            "api_key": self._create_api_key(),
            "created_at": datetime.utcnow(),
            "favourites": kwargs.get("favourites") or list(),
            "id": self.users.find().count() + 1,
            "is_banned": kwargs.get("is_banned") or False,
            "pass_hash": generate_password_hash(kwargs.get("password")),
            "permissions": kwargs.get("permissions") or 1,
            "settings": kwargs.get("settings") or dict(),
            "username": kwargs.get("username") or self._random_username(),
        }

        # insert the dict
        insert = self.users.insert_one(user_data)
        log.debug(
            f"""User "{user_data.get("username")}" inserted into Database with _id "{insert.inserted_id}\""""
        )
        return

    def add_collection(self, data: [list, dict]):
        pass

    def add_tag(self, data: [list, dict]):
        pass

    ## GETTING

    def get_user(self, id=None, username=None, api_key=None) -> User:
        if id is not None:
            # Check for user with ID
            user = self.users.find_one({"id": id})
            if user is None:
                raise ValueError("Supplied ID does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("id")}) with ID."""
            )

        elif username is not None:
            # Check for user with Username
            user = self.users.find_one(
                {"username": re.compile(username, re.IGNORECASE)}
            )
            if user is None:
                raise ValueError("Supplied Username does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("id")}) with Username."""
            )

        elif api_key is not None:
            # Check for user with API key
            user = self.users.find_one({"api_key": api_key})
            if user is None:
                raise ValueError("Supplied API Key does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("id")}) with API key."""
            )
        else:
            raise ValueError("One of: id, username, api_key must be supplied.")

        return User(
            self,
            user.get("id"),
            user.get("username"),
            UserPermissions(user.get("permissions") or 1),
            user.get("is_banned"),
            user.get("favourites"),
            user.get("settings"),
            user.get("api_key"),
            user.get("created_at"),
            user.get("pfp"),
            user.get("bio"),
        )

    def get_raw_tag_info(self, tag_string: str) -> dict:
        # return raw tag data from database
        return dict()

    ## INTERNAL FUNCTIONS

    def _parse_tags(self, tags: list) -> list:
        tgs = set()
        for tag in tags:
            tgs.add(tag.strip().replace(" ", "_").lower())
        return list(tgs)

    def _random_username(self) -> str:
        return "User_" + "".join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for x in range(6)
        )

    def _create_api_key(self) -> str:
        return hexlify(os.urandom(20)).decode()
