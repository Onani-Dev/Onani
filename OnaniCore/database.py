# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-17 00:09:05

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
    def add_post(self, file_url=None, thumb_url=None, tags=list(), meta=dict()) -> None:
        # add a post to the database
        post_data = {
            "id": self.posts.find().count() + 1,
            # Need to use file controller here!
            "file_url": file_url,
            "thumb_url": thumb_url,
            "tags": tags,
            "meta": meta,
        }
        # TODO #10 need to add extra logic to database add_post method
        insert = self.posts.insert_one(post_data)
        log.debug(
            f"""Inserted post {post_data.get("id")} with _id {insert.inserted_id}"""
        )
        return

    def add_user(
        self,
        username: str = None,
        is_banned: bool = False,
        favourites: list = list(),
        permissions: UserPermissions = UserPermissions.MEMBER,
        settings: dict = dict(),
        password: str = None,
    ) -> None:
        # add a user to the database
        if password is None:
            # We didnt recieve a password
            raise ValueError("Accounts MUST have a password.")
        if username is None:
            username = self._random_username()
        # Check if Username is already taken, If one is supplied.
        user = self.users.find_one({"username": re.compile(username, re.IGNORECASE)})
        if user is not None:
            # We can't use this username.
            raise ValueError("Username is taken.")
        log.debug(f""""{username}" looks good to use.""")

        # Construct dict to insert into database
        user_data = {
            "id": self.users.find().count() + 1,
            "username": username,
            "api_key": self._create_api_key(),
            "created_at": datetime.utcnow(),
            "is_banned": is_banned,
            "favourites": favourites,
            "permissions": permissions.value,
            "settings": settings,
            "pass_hash": generate_password_hash(password),
        }

        # insert the dict
        insert = self.users.insert_one(user_data)
        log.debug(
            f"""User \"{user_data.get("username")}\" inserted into Database with _id \"{insert.inserted_id}\""""
        )
        return

    def add_collection(self, data: [list, dict]):
        pass

    def add_tag(self, data: [list, dict]):
        pass

    def add_ban(self, user: User, reason: str = None) -> None:
        # add a ban for a user
        self.bans.insert_one({"user_id": user.id, "reason": reason})
        self.users.update_one(
            {"username": user.username}, {"$set": {"is_banned": True}}
        )
        return

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
            user.get("is_banned") or False,
            user.get("favourites") or list(),
            user.get("settings") or dict(),
            user.get("api_key"),
            user.get("created_at"),
        )

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
