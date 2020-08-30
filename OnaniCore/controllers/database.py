# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-31 00:47:30

import logging
import os
import random
import re
import secrets
import string
from datetime import datetime, timedelta
from timeit import timeit
from typing import Dict, List, Tuple

import pymongo
from passlib.hash import argon2

from ..models import Post, Tag, TagType, User, UserPermissions, UserSettings, PostFile

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

    ## POSTS
    def add_post(self, file: PostFile = None, tags=list(), data=dict()) -> Post:
        # add a post to the database
        post_data = {
            "_id": self.posts.count_documents({}) + 1,
            "file": file.to_dict(),
            "tags": tags,
            "data": data,
        }
        # TODO #10 need to add extra logic to database add_post method
        insert = self.posts.insert_one(post_data)
        log.debug(f"""Inserted post {insert.inserted_id}""")

    ## USERS
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
            "_id": self.users.count_documents({}) + 1,
            "username": username,
            "api_key": self._create_api_key(),
            "created_at": datetime.utcnow(),
            "favourites": favourites,
            "permissions": permissions.value,
            "settings": settings.to_dict(),
            "pass_hash": argon2.using(rounds=6).hash(password),
            "is_active": True,
        }

        # insert the dict
        insert = self.users.insert_one(user_data)
        log.debug(
            f"""User \"{user_data.get("username")}\" inserted into Database with _id \"{insert.inserted_id}\""""
        )
        return self.get_user(id=insert.inserted_id)

    def get_user(self, id=None, username=None, api_key=None) -> User:
        if id is not None:
            # Check for user with ID
            user = self.users.find_one({"_id": id})
            if user is None:
                raise ValueError("Supplied ID does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with ID."""
            )

        elif username is not None:
            # Check for user with Username
            user = self.users.find_one(
                {"username": re.compile(username, re.IGNORECASE)}
            )
            if user is None:
                raise ValueError("Supplied Username does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with Username."""
            )

        elif api_key is not None:
            # Check for user with API key
            user = self.users.find_one({"api_key": api_key})
            if user is None:
                raise ValueError("Supplied API Key does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with API key."""
            )
        else:
            raise ValueError("One of: id, username, api_key must be supplied.")

        # Return our user
        return User(
            self,
            user.get("_id"),
            user.get("username"),
            UserPermissions(user.get("permissions")),
            user.get("favourites") or list(),
            UserSettings(**user.get("settings")),
            user.get("api_key"),
            user.get("created_at"),
            user.get("is_active"),
            user.get("pass_hash"),
        )

    def modify_user(
        self,
        user: User,
        username: str = None,
        settings: dict = None,
        permissions: UserPermissions = None,
    ) -> None:
        # Edit username if present
        if username is not None:
            existing_user = self.users.find_one(
                {"username": re.compile(username, re.IGNORECASE)}
            )
            if existing_user is not None:
                # We can't use this username.
                raise ValueError("Username is taken.")
            self.users.update_one({"_id": user.id}, {"$set": {"username": username}})
            user.username = username

        # Edit settings if present
        if settings is not None:
            user.settings.update(**settings)
            self.users.update_one(
                {"_id": user.id}, {"$set": {"settings": user.settings.to_dict()}}
            )

        # Edit permissions if present
        if permissions is not None:
            self.users.update_one(
                {"_id": user.id}, {"$set": {"permissions": permissions.value}}
            )
            user.permissions = permissions

    def regen_user_api_key(self, user: User) -> None:
        # regen api key for user
        api_key = self._create_api_key()
        self.users.update_one({"_id": user.id}, {"$set": {"api_key": api_key}})
        user.api_key = api_key

    def add_user_favourite(self, user: User, post: Post) -> None:
        # add a post to user favourites
        update = self.users.update_one(
            {"_id": user.id}, {"$addToSet": {"favourites": post.id}}
        )
        if update.modified_count > 0:
            user.favourites.append(post.id)
            log.debug(f"Post {post.id} was added to {user.username}'s Favourites")
        else:
            log.debug("Post was not added as it already exists as a favourite.")

    def remove_user_favourite(self, user: User, post: Post) -> None:
        # remove a post from user favourites
        update = self.users.update_one(
            {"_id": user.id}, {"$pull": {"favourites": post.id}}
        )
        if update.modified_count > 0:
            user.favourites.remove(post.id)
            log.debug(f"Post {post.id} was removed from {user.username}'s Favourites")
        else:
            log.debug("Post was not removed as it does not exist as a favourite.")

    def add_user_ban(
        self,
        user: User,
        reason: str = None,
        duration: timedelta = timedelta(days=30),
        ban_creator: User = None,
    ) -> None:
        # add a ban for a user
        # TODO #21 Add who issued ban and when
        # Check if a ban already exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is not None:
            # there is already a ban for this user
            raise ValueError("This user is already banned")

        # create dict and add the ban to the database
        ban_data = {
            "user_id": user.id,
            "reason": reason,
            "ban_creator_id": ban_creator.id,
            "since": datetime.utcnow(),
            "expires": datetime.utcnow() + duration,
        }
        self.bans.insert_one(ban_data)

        # give the user BANNED perms
        self.users.update_one(
            {"username": user.username, "_id": user.id},
            {"$set": {"permissions": UserPermissions.BANNED.value}},
        )
        log.info(
            f"{user.username} (ID: {user.id}) has been banned with reason: {reason}."
        )
        user.permissions = UserPermissions.BANNED

    def remove_user_ban(self, user: User) -> None:
        # Remove a ban for a user

        # Check if a ban exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is None:
            # there is no existing ban
            raise ValueError("This user is not banned")

        self.bans.delete_one({"user_id": user.id})

        # remove the BANNED perms
        self.users.update_one(
            {"username": user.username, "_id": user.id},
            {"$set": {"permissions": UserPermissions.MEMBER.value}},
        )
        log.info(f"{user.username} (ID: {user.id}) has been unbanned")
        user.permissions = UserPermissions.MEMBER

    ## TAGS
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

    def add_tag_alias(self, tag: Tag, alias: str) -> None:
        # add an alias to a tag
        alias = self._parse_tag(alias)
        update = self.tags.update_one(
            {"string": tag.string}, {"$addToSet": {"aliases": alias}}
        )
        if update.modified_count > 0:
            tag.aliases.append(alias)
            log.debug(f'Alias added for tag "{tag.string}"')
        else:
            log.debug("Alias was not added as it already exists.")

    def get_tag(self, tag_string: str) -> Tag:
        # Find a tag in the database with the provided name
        tag = self.tags.find_one({"string": re.compile(tag_string, re.IGNORECASE)})
        if tag is None:
            tag = self.tags.find_one({"aliases": re.compile(tag_string, re.IGNORECASE)})
            if tag is None:
                raise ValueError(
                    f'No tag mathching the name "{tag_string}" could be found.'
                )
        log.debug(f'Tag found with name "{tag_string}"')

        # return our tag
        return Tag(
            self,
            tag.get("string"),
            TagType(tag.get("type")),
            tag.get("aliases"),
            tag.get("description"),
        )

    def get_tags(
        self,
        limit: int = 100,
        tag_regex: str = None,
        sort: str = "_id",
        sort_direction: int = pymongo.DESCENDING,
        tag_strings: list = None,
    ) -> List[Tag]:
        # Check if list of tag strings is present ( Limit ingored )
        if tag_strings is not None:
            # get all the tag strings.
            found_tags = list(self.tags.find({"string": {"$in": tag_strings}}))
            found_tags.extend(list(self.tags.find({"aliases": {"$in": tag_strings}})))

        else:
            # get tags with regex
            if tag_regex is None:
                # Find all
                found_tags = self.tags.find().limit(limit).sort(sort, sort_direction)
            else:
                # Find with regex
                found_tags = list(
                    self.tags.find({"string": re.compile(tag_regex, re.IGNORECASE)})
                    .limit(limit)
                    .sort(sort, sort_direction)
                )
                found_tags.extend(
                    list(
                        self.tags.find(
                            {"aliases": re.compile(tag_regex, re.IGNORECASE),}
                        )
                        .limit(limit)
                        .sort(sort, sort_direction)
                    )
                )
        # return a list of Tag objects
        return [
            Tag(
                self,
                x.get("string"),
                TagType(x.get("type")),
                x.get("aliases"),
                x.get("description"),
            )
            for x in found_tags
        ]

    def remove_tag_alias(self, tag: Tag, alias: str) -> None:
        # add an alias to a tag
        update = self.tags.update_one(
            {"string": tag.string}, {"$pull": {"aliases": alias}}
        )
        if update.modified_count > 0:
            tag.aliases.remove(alias)
            log.debug(f'Alias removed for tag "{tag.string}"')
        else:
            log.debug("Alias was not removed as it doesnt't exist.")

    def modify_tag(
        self,
        tag: Tag,
        tag_string: str = None,
        tag_type: TagType = None,
        description: str = None,
    ) -> None:
        # Update string if present
        if tag_string is not None:
            tag_string = self._parse_tag(tag_string)
            self.tags.update_one(
                {"string": tag.string}, {"$set": {"string": tag_string}},
            )
            tag.string = tag_string
            log.debug(f'Tag name changed to "{tag.string}"')

        # update type if present
        if tag_type is not None:
            self.tags.update_one(
                {"string": tag.string}, {"$set": {"type": tag_type.value}},
            )
            tag.type = tag_type
            log.debug(f'Type changed to "{tag_type.string}" for tag "{tag.string}"')

        # update description if present
        if description is not None:
            self.tags.update_one(
                {"string": tag.string}, {"$set": {"description": description}},
            )
            tag.description = description
            log.debug(f'Description changed for tag "{tag.string}"')

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
        return secrets.token_urlsafe(32)
