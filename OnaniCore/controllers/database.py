# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-12 19:50:22
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-07 22:00:22

from OnaniCore.models.file import File
import random
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import List

import pymongo
from dateutil import tz
from passlib.hash import argon2

from ..exceptions import OnaniAuthenticationError, OnaniDatabaseException
from ..models import (
    Ban,
    Post,
    PostData,
    Tag,
    TagType,
    User,
    UserPermissions,
    UserPlatforms,
    UserSettings,
)
from ..utils import setup_logger
from .files import FileController

log = setup_logger(__name__)


class DatabaseController:
    """
    Controller for the Onani Database
    """

    __slots__ = (
        "bans",
        "client",
        "collections",
        "db",
        "file_controller",
        "posts",
        "tags",
        "users",
    )

    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/"):
        # Connect to the mongoDB instance
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client["OnaniDB"]
        self.bans = self.db["OnaniBans"]
        self.collections = self.db["OnaniCollections"]
        self.posts = self.db["OnaniPosts"]
        self.tags = self.db["OnaniTags"]
        self.users = self.db["OnaniUsers"]

        # Create indexes if they don't exist
        self.tags.create_index("string")
        self.tags.create_index("aliases")
        self.users.create_index("username")

        # Create a file controller for this DatabaseController Instance
        self.file_controller = FileController()

    ## POSTS
    def add_post(self, filedata: File, tags: List[Tag], data: PostData) -> Post:
        """```raw
        Add a post to the database

        Args:
            filedata (File): The Post File
            tags (List[Tag]): The list of Tag objects for this post
            data (PostData): The post data

        Returns:
            Post: The Post method
        """
        post_data = {
            "_id": self.posts.count_documents({}) + 1,
            "file": filedata.to_dict(),
            "tags": tags,
            "data": data.to_dict(),
        }
        insert = self.posts.insert_one(post_data)
        log.debug(f"""Inserted post {insert.inserted_id}""")

        # get post and return
        return self.get_post(insert.inserted_id)

    def get_post(self, id: int) -> Post:
        """```raw
        Get a post from the database

        Args:
            id (int): The posts ID

        Raises:
            OnaniDatabaseException: The ID was not found in the database

        Returns:
            Post: The found post
        """
        post = self.posts.find_one({"_id": id})
        if post is None:
            # no post found
            raise OnaniDatabaseException(
                "The specified ID could not be found in the database."
            )

        # Return post
        return Post(
            db=self,
            post_id=post.get("_id"),
            file_data=post.get("file"),
            tags=post.get("tags"),
            data=post.get("data"),
        )

    def edit_post(self, post: Post, post_data: dict = None, tags: list = None):
        pass

    ## USERS
    def add_user(
        self,
        username: str = None,
        email: str = None,
        favourites: list = list(),
        permissions: UserPermissions = UserPermissions.MEMBER,
        settings: UserSettings = UserSettings(),
        password: str = None,
    ) -> User:
        """```raw
        Add a user to the database

        Args:
            username (str, optional): The uername for the user. Defaults to a Random Username.
            email (str, optional): Email for the user. Defaults to None.
            favourites (list, optional): Favourites for the user. Defaults to list().
            permissions (UserPermissions, optional): The users permissions. Defaults to UserPermissions.MEMBER.
            settings (UserSettings, optional): Settings for the user. Defaults to UserSettings().
            password (str): The User's password. Defaults to None.

        Raises:
            OnaniDatabaseException: Raised when password not given
            OnaniDatabaseException: Raised when Username is taken

        Returns:
            User: The User object
        """
        if password is None:
            # We didnt recieve a password
            raise OnaniDatabaseException("Accounts MUST have a password.")
        if username is None:
            username = self._random_username()

        # Check if Username is already taken.
        user = self.users.find_one(
            {"username": re.compile(fr"\b{username}\b", re.IGNORECASE)}
        )
        if user is not None:
            # We can't use this username.
            raise OnaniDatabaseException("Username is taken.")

        # Check if email is already used, If one is supplied.
        if email is not None:
            user = self.users.find_one({"email": email})
            if user is not None:
                # We can't use this email.
                raise OnaniDatabaseException("Email is already in use.")

        log.debug(f""""{username}" looks good to use.""")

        # Construct dict to insert into database
        user_data = {
            "_id": self.users.count_documents({}) + 1,
            "username": username,
            "email": email,
            "api_key": self._create_api_key(),
            "created_at": datetime.utcnow().replace(tzinfo=tz.tzutc()),
            "favourites": favourites,
            "permissions": permissions.value,
            "settings": settings.to_dict(),
            "pass_hash": argon2.using(rounds=6).hash(password),
            "is_active": True,
        }

        # insert the dict
        insert = self.users.insert_one(user_data)

        # Log to database
        log.info(
            f'User {user_data.get("username")} ({insert.inserted_id}): Account Created'
        )

        # Return user object
        return self.get_user(id=insert.inserted_id)

    def get_user(
        self,
        id: int = None,
        username: str = None,
        email: str = None,
        api_key: str = None,
    ) -> User:
        """```raw
        Get a user from the database

        Args:
            id (int, optional): The user's ID. Defaults to None.
            username (str, optional): The user's Username. Defaults to None.
            email (str, optional): The user's email. Defaults to None.
            api_key (str, optional): The user's API key. Defaults to None.

        Raises:
            OnaniDatabaseException: Supplied value did not exist in database

        Returns:
            User: The Found User
        """
        if id is not None:
            # Check for user with ID
            user = self.users.find_one({"_id": id})
            if user is None:
                raise OnaniDatabaseException("Supplied ID does not exist in Database.")
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with ID."""
            )

        elif username is not None:
            # Check for user with Username
            user = self.users.find_one(
                {"username": re.compile(fr"\b{username}\b", re.IGNORECASE)}
            )
            if user is None:
                raise OnaniDatabaseException(
                    "Supplied Username does not exist in Database."
                )
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with Username."""
            )

        elif email is not None:
            # Check for user with Email
            user = self.users.find_one({"email": email})
            if user is None:
                raise OnaniDatabaseException(
                    "Supplied email does not exist in Database."
                )
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with Email."""
            )

        elif api_key is not None:
            # Check for user with API key
            user = self.users.find_one({"api_key": api_key})
            if user is None:
                raise OnaniDatabaseException(
                    "Supplied API Key does not exist in Database."
                )
            log.debug(
                f"""Found user {user.get("username")} (ID: {user.get("_id")}) with API key."""
            )
        else:
            raise OnaniDatabaseException(
                "One of: id, username, api_key must be supplied."
            )

        # Make platforms object
        if user.get("settings"):
            user["settings"]["platforms"] = UserPlatforms(
                **user["settings"]["platforms"]
            )
            user["settings"]["avatar"] = File(**user["settings"]["avatar"])

        # Return our user
        return User(
            db=self,
            id=user.get("_id"),
            username=user.get("username"),
            email=user.get("email"),
            permissions=UserPermissions(user.get("permissions")),
            favourites=user.get("favourites") or list(),
            settings=UserSettings(**user.get("settings")),
            api_key=user.get("api_key"),
            created_at=user.get("created_at"),
            is_active=user.get("is_active"),
            pass_hash=user.get("pass_hash"),
        )

    def add_user_favourite(self, user: User, post: Post) -> None:
        """```raw
        Add a post to user favourites

        Args:
            user (User): The user to add the favourite to
            post (Post): The post to favourite
        """
        update = self.users.update_one(
            {"_id": user.id}, {"$addToSet": {"favourites": post.id}}
        )
        if update.modified_count > 0:
            user.favourites.append(post.id)
            log.debug(f"Post {post.id} was added to {user.username}'s Favourites")
        else:
            log.debug("Post was not added as it already exists as a favourite.")

    def remove_user_favourite(self, user: User, post: Post) -> None:
        """```raw
        Remove a post from user favourites

        Args:
            user (User): The user to remove the favourite from
            post (Post): The post to unfavourite
        """

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
    ) -> Ban:
        """```raw
        Give a user the BANNED permissions and add a ban to the Ban database

        Args:
            user (User): The user to ban
            reason (str, optional): A reason for this ban. Defaults to None.
            duration (timedelta, optional): Time this user will be banned for. Defaults to timedelta(days=30).
            ban_creator (User, optional): The user who initiated this ban. Defaults to None.

        Raises:
            OnaniDatabaseException: If the user is already banned

        Returns:
            Ban: The ban object
        """

        # Check if a ban already exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is not None:
            # there is already a ban for this user
            raise OnaniDatabaseException("This user is already banned")

        # create dict and add the ban to the database
        ban_data = {
            "user_id": user.id,
            "reason": reason,
            "ban_creator_id": ban_creator.id,
            "since": datetime.utcnow().replace(tzinfo=tz.tzutc()),
            "expires": datetime.utcnow().replace(tzinfo=tz.tzutc()) + duration,
        }
        self.bans.insert_one(ban_data)

        # give the user BANNED perms
        self.users.update_one(
            {"username": user.username, "_id": user.id},
            {"$set": {"permissions": UserPermissions.BANNED.value}},
        )
        log.info(f"User {user.username} ({user.id}): Banned with reason: {reason}.")
        user.permissions = UserPermissions.BANNED

    def remove_user_ban(self, user: User) -> None:
        """```raw
        Remove a ban for a User, Removes the permissions and the ban database entry

        Args:
            user (User): The user to unban

        Raises:
            OnaniDatabaseException: If the user is not banned
        """

        # Check if a ban exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is None:
            # there is no existing ban
            raise OnaniDatabaseException("This user is not banned")

        self.bans.delete_one({"user_id": user.id})

        # remove the BANNED perms
        self.users.update_one(
            {"username": user.username, "_id": user.id},
            {"$set": {"permissions": UserPermissions.MEMBER.value}},
        )
        log.info(f"{user.username} (ID: {user.id}) has been unbanned")
        user.permissions = UserPermissions.MEMBER

    def get_user_ban(self, user: User) -> Ban:
        """```raw
        Get a user ban from the database

        Args:
            user (User): User to retrieve the ban for

        Raises:
            OnaniDatabaseException: If the user isn't banned

        Returns:
            Ban: The Ban object
        """
        # Check if a ban exists
        ban = self.bans.find_one({"user_id": user.id})
        if ban is None:
            # there is no existing ban
            raise OnaniDatabaseException("This user is not banned")
        return Ban(
            self,
            self.get_user(id=ban.get("user_id")),
            ban.get("reason"),
            self.get_user(id=ban.get("ban_creator_id")),
            ban.get("since"),
            ban.get("expires"),
        )

    ## TAGS
    def add_tag(
        self,
        tag_string: str,
        tag_type: TagType = TagType.GENERAL,
        aliases: list = list(),
        description: str = None,
        post_count: int = 0,
        popularity: float = 0.0,
    ) -> Tag:
        """```raw
        Add a tag to the database

        Args:
            tag_string (str): The tag string, (Automatically stripped and whitespace replaced with _)
            tag_type (TagType, optional): The tags type. Defaults to TagType.GENERAL.
            aliases (list, optional): Aliases for this tag. Defaults to list().
            description (str, optional): This tags description. Defaults to None.
            post_count (int, optional): The amount of posts with this tag. Defaults to 0.
            popularity (float, optional): The popularity of this tag. Defaults to 0.0.

        Raises:
            OnaniDatabaseException: Raised when a tag with this name already exists.

        Returns:
            Tag: The Tag object
        """
        tag_string = self._parse_tag(tag_string)

        tag = self.tags.find_one(
            {"string": re.compile(fr"\b{tag_string}\b", re.IGNORECASE)}
        )
        if tag is not None:
            # What the OnaniDatabaseException says :)
            raise OnaniDatabaseException("A tag with this name already exists.")

        # Create dict and insert
        tag_data = {
            "_id": self.tags.count_documents({}) + 1,
            "string": tag_string,
            "type": tag_type.value,
            "aliases": aliases,
            "description": description,
            "post_count": post_count,
            "popularity": popularity,
        }
        insert = self.tags.insert_one(tag_data)
        log.debug(
            f"Tag \"{tag_data.get('string')}\" inserted into Database with _id \"{insert.inserted_id}\""
        )
        return self.get_tag(tag_id=insert.inserted_id)

    def get_tag(self, tag_id: int = None, tag_string: str = None) -> Tag:
        """```raw
        Find a tag in the database with the provided name or ID

        Args:
            tag_id (int, optional): The ID of the tag to look for. Defaults to None.
            tag_string (str, optional): The string of the tag or alias to look for. Defaults to None.

        Raises:
            ValueError: Nothing was supplied
            OnaniDatabaseException: No match found

        Returns:
            Tag: The found tag
        """
        # Check if Tag ID is present
        if tag_id:
            # Find em
            tag = self.tags.find_one({"_id": tag_id})
            if not tag:
                raise OnaniDatabaseException(
                    f"No tag mathching the ID {tag_id} could be found."
                )
            log.debug(f'Tag found with ID "{tag_id}"')

        # Check with tag string
        elif tag_string:
            tag = self.tags.find_one(
                {"string": re.compile(fr"\b{tag_string}\b", re.IGNORECASE)}
            )
            if not tag:
                # Maybe an alias?
                tag = self.tags.find_one(
                    {"aliases": re.compile(fr"\b{tag_string}\b", re.IGNORECASE)}
                )
                if not tag:
                    # Not an alias. Doesn't exist
                    raise OnaniDatabaseException(
                        f'No tag mathching the name "{tag_string}" could be found.'
                    )
            log.debug(f'Tag found with name "{tag_string}"')

        # Nothing.
        else:
            # You are a loser
            raise ValueError("No argument was supplied.")

        # return our tag
        return Tag(
            db=self,
            id=tag.get("_id"),
            tag_string=tag.get("string"),
            tag_type=TagType(tag.get("type")),
            aliases=tag.get("aliases"),
            description=tag.get("description"),
            post_count=tag.get("post_count"),
            popularity=tag.get("popularity"),
        )

    def get_tags(
        self,
        limit: int = 100,
        tag_regex: str = None,
        sort: str = "_id",
        sort_direction: int = pymongo.DESCENDING,
        tag_strings: list = None,
        tag_ids: list = None,
    ) -> List[Tag]:
        """```raw
        Find tags in the database with the provided regex or list of tag strings

        Args:
            limit (int, optional): Defaults to 100.
            tag_regex (str, optional): Regex to match for the tags. Defaults to None.
            sort (str, optional): The order to sort the tags by. Defaults to "_id".
            sort_direction (int, optional): The Direction to sort. Defaults to pymongo.DESCENDING.
            tag_strings (list, optional): l. Defaults to None.
            tag_ids (list, optional): The tag IDs to find. Defaults to None.

        Returns:
            List[Tag]: List of Tag found tag objects
        """

        # Check if list of tag IDs is present
        if tag_ids:
            # Find the tags with supplied IDs
            found_tags = list(self.tags.find({"_id": {"$in": tag_ids}}))

        # Check if list of tag strings is present ( Limit ingored )
        elif tag_strings:
            # get all the tag strings.
            found_tags = list(self.tags.find({"string": {"$in": tag_strings}}))
            found_tags.extend(list(self.tags.find({"aliases": {"$in": tag_strings}})))

        else:
            # get tags with regex
            if not tag_regex:
                # Find all
                found_tags = list(
                    self.tags.find().limit(limit).sort(sort, sort_direction)
                )
            else:
                # Find with regex
                found_tags = list(
                    self.tags.find({"string": re.compile(tag_regex, re.IGNORECASE)})
                    .limit(limit)
                    .sort(sort, sort_direction)
                )
                # Extend with aliases
                found_tags.extend(
                    list(
                        self.tags.find(
                            {"aliases": re.compile(tag_regex, re.IGNORECASE),}
                        )
                        .limit(limit)
                        .sort(sort, sort_direction)
                    )
                )
        log.debug(f"Found {len(found_tags)} Tags.")
        # return a list of Tag objects
        return [
            Tag(
                db=self,
                id=x.get("_id"),
                tag_string=x.get("string"),
                tag_type=TagType(x.get("type")),
                aliases=x.get("aliases"),
                description=x.get("description"),
                post_count=x.get("post_count"),
                popularity=x.get("popularity"),
            )
            for x in found_tags
        ]

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

    def _sanitize(self, query: str) -> str:
        return query.replace("function()", "")
