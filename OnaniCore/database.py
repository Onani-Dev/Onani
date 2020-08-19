# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-19 23:56:52

import logging
import os
import random
import re
import string
from binascii import hexlify
from datetime import datetime, timedelta

import pymongo
from werkzeug.security import generate_password_hash

from .post import Post
from .tag import Tag, TagType
from .user import User, UserPermissions, UserSettings

log = logging.getLogger(__name__)


class DatabaseController:
    """
    Controller for the Onani Database
    """

    __slots__ = ("client", "db", "posts", "tags", "users", "collections", "bans")

    def __init__(
        self, mongo_uri: str = "mongodb://localhost:27017/",
    ):
        self.client = pymongo.MongoClient(mongo_uri)
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
        favourites: list = list(),
        permissions: UserPermissions = UserPermissions.MEMBER,
        settings: UserSettings = UserSettings(),
        password: str = None,
    ) -> User:
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
            "favourites": favourites,
            "permissions": permissions.value,
            "settings": settings.to_dict(),
            "pass_hash": generate_password_hash(password),
        }

        # insert the dict
        insert = self.users.insert_one(user_data)
        log.debug(
            f"""User \"{user_data.get("username")}\" inserted into Database with _id \"{insert.inserted_id}\""""
        )
        return self.get_user(mongo_id=insert.inserted_id)

    def add_user_ban(
        self, user: User, reason: str = None, duration: timedelta = timedelta(days=30)
    ) -> None:
        # add a ban for a user

        # Check if a ban already exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is not None:
            # there is already a ban for this user
            raise ValueError("This user is already banned")

        # create dict and add the ban to the database
        ban_data = {
            "user_id": user.id,
            "reason": reason,
            "expires": datetime.utcnow() + duration,
        }
        self.bans.insert_one(ban_data)

        # give the user BANNED perms
        self.users.update_one(
            {"username": user.username, "id": user.id},
            {"$set": {"permissions": UserPermissions.BANNED.value}},
        )
        log.info(
            f"{user.username} (ID: {user.id}) has been banned with reason: {reason}."
        )
        return

    def add_tag(
        self,
        tag_string: str,
        tag_type: TagType = TagType.GENERAL,
        aliases: list = list(),
        description: str = None,
    ) -> Tag:
        # add a tag to the database
        tag_string = self._parse_tag(tag_string)

        tag = self.tags.find_one({"string": re.compile(tag_string, re.IGNORECASE)})
        if tag is not None:
            # What the ValueError says :)
            raise ValueError("A tag with this name already exists.")

        # Create dict and insert
        tag_data = {
            "string": tag_string,
            "type": tag_type.value,
            "aliases": aliases,
            "description": description,
        }
        insert = self.tags.insert_one(tag_data)
        log.debug(
            f"Tag \"{tag_data.get('string')}\" inserted into Database with _id \"{insert.inserted_id}\""
        )
        return self.get_tag(tag_data.get("string"))

    def add_tag_ban(self, tag: Tag) -> None:
        # ban a tag
        self.tags.update_one(
            {"string": tag.string}, {"$set": {"type": TagType.BANNED.value}},
        )
        return

    def add_tag_alias(self, tag: Tag, alias: str) -> [str, None]:
        # add an alias to a tag
        update = self.tags.update_one(
            {"string": tag.string}, {"$addToSet": {"aliases": self._parse_tag(alias)}}
        )
        return self._parse_tag(alias) if update.modified_count > 0 else None

    ## GETTING

    def get_user(self, id=None, username=None, api_key=None, mongo_id=None) -> User:
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

        elif mongo_id is not None:
            # Check for user with a mongo document ID
            user = self.users.find_one({"_id": mongo_id})
            if user is None:
                raise ValueError(
                    "Supplied Mongo Document ID does not exist in Database."
                )
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("id")}) with MongoDB ID."""
            )

        else:
            raise ValueError("One of: id, username, api_key must be supplied.")

        # Return our user
        return User(
            self,
            user.get("id"),
            user.get("username"),
            UserPermissions(user.get("permissions")),
            user.get("favourites") or list(),
            UserSettings(**user.get("settings")),
            user.get("api_key"),
            user.get("created_at"),
        )

    def get_tag(self, tag_string: str):
        # Find a tag in the database with the provided name
        tag = self.tags.find_one({"string": re.compile(tag_string, re.IGNORECASE)})
        if tag is None:
            tag = self.tags.find_one({"aliases": re.compile(tag_string, re.IGNORECASE)})
            if tag is None:
                raise ValueError(
                    f'No tag mathching the name "{tag_string}" could be found.'
                )

        # return our tag
        return Tag(
            self,
            tag.get("string"),
            TagType(tag.get("type")),
            aliases=tag.get("aliases"),
            description=tag.get("description"),
        )

    ## REMOVING

    def remove_tag_alias(self, tag: Tag, alias: str) -> [str, None]:
        # add an alias to a tag
        update = self.tags.update_one(
            {"string": tag.string}, {"$pull": {"aliases": alias}}
        )
        return alias if update.modified_count > 0 else None

    def remove_tag_ban(self, tag: Tag, type: TagType = TagType.GENERAL):
        # TODO #14 #13 add remove_tag_ban and modify_tag
        pass

    ## MODIFYING

    def modify_tag(self, tag: Tag, **kwargs):
        pass

    ## INTERNAL FUNCTIONS

    def _parse_tag(self, tag: str) -> str:
        return tag.strip().replace(" ", "_").lower()

    def _parse_tags(self, tags: list) -> list:
        tgs = set()
        for tag in tags:
            tgs.add(self._parse_tag(tag))
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
