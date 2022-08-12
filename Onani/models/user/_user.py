# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 23:57:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 15:41:20

from __future__ import annotations

import datetime
import html
import secrets
import string
import uuid
from typing import TYPE_CHECKING, List, Optional, Union

import regex as re
from flask_login import UserMixin
from Onani.controllers.utils import colour_contrast
from passlib.hash import argon2
from sqlalchemy.orm import validates
from sqlalchemy.orm.query import Query
from sqlalchemy_utils import ChoiceType

from . import Ban, db
from .permissions import UserPermissions
from .roles import UserRoles
from .settings import UserSettings

if TYPE_CHECKING:
    from Onani.models import Post


tag_blacklist = db.Table(
    "tag_blacklist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)


class User(UserMixin, db.Model):
    """
    User Models, these represent users on onani, and can be logged in to.
    """

    __tablename__ = "users"

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.settings:
            self.settings = UserSettings()

    #
    id: int = db.Column(db.Integer, primary_key=True)
    """Users ID, obviously unique as it is the primary key"""

    #
    username: str = db.Column(db.String, index=True, unique=True, nullable=False)
    """Users username, must be unique and may not be changed unless absolutely neccesary"""

    nickname: str = db.Column(db.String, unique=True)
    """Like a username, except that it can't be used to login and can be changed freely."""

    email: str = db.Column(db.String, index=True, unique=True)
    """Users email, optional and must be unique"""

    password_hash: str = db.Column(db.String, nullable=False)
    """The argon2 hash of the users password."""

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    """The time this user was created. it doesn't need to be touched."""

    role: UserRoles = db.Column(
        ChoiceType(UserRoles, impl=db.Integer()),
        default=UserRoles.MEMBER,
        nullable=False,
    )
    """The User's role. this affects what permissions the user can utilize"""

    permissions: UserPermissions = db.Column(
        ChoiceType(UserPermissions, impl=db.Integer()),
        default=UserPermissions.DEFAULT,
        nullable=False,
    )
    """The user's permissions. this contains flags on what a user can do."""

    api_key: str = db.Column(
        db.String,
        index=True,
        unique=True,
        default=lambda: secrets.token_urlsafe(32),
    )
    """The api key the user will use for the /api endpoint. Grants full control over the user account"""

    ban: Optional[Ban] = db.relationship(Ban, uselist=False, backref="user_ban")
    """The ban that this user has. will be None if not banned."""

    tag_blacklist: Query = db.relationship(
        "Tag",
        secondary=tag_blacklist,
        backref="user_blacklist",
        lazy="dynamic",
    )
    """The tag blacklist. posts with tags on this list will not appear on this user's results."""

    settings: UserSettings = db.relationship(
        "UserSettings", uselist=False, backref="user_settings"
    )
    """The user's settings. eg. custom css or profile connections"""

    comments: Query = db.relationship(
        "PostComment", backref="user_comments", lazy="dynamic", viewonly=True
    )
    """The users comments on posts."""

    posts: Query = db.relationship(
        "Post", backref="user_posts", lazy="dynamic", viewonly=True
    )
    """The users uploaded posts."""

    post_count: int = db.Column(db.Integer, default=0, nullable=False)
    """Amount of posts this user has uploaded."""

    login_id: str = db.Column(
        db.String, index=True, unique=True, default=lambda: str(uuid.uuid4())
    )
    """ULTRA SECRET LOGIN UUID FOR INTERNAL LOGGING IN!!!!1!!!1 (hidden value for securely logging in users with flask-login)"""

    is_deleted: bool = db.Column(db.Boolean, default=False)
    """If the user deletes their account, this will become true."""

    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise ValueError("No username provided")

        if len(username) < 3 or len(username) > 32:
            raise ValueError("Username must be between 3 and 32 characters")

        for c in username:
            if c not in string.ascii_letters + string.digits + string.punctuation:
                raise ValueError(f'Invalid Character in username. ("{c}")')

        if User.query.filter(User.username == username).first():
            raise ValueError("Username is already in use")

        return html.escape(username)

    @validates("nickname")
    def validate_nickname(self, key, nickname):
        if not nickname:
            return None

        if len(nickname) < 3 or len(nickname) > 32:
            raise ValueError("Nickname must be between 3 and 32 characters")

        return html.escape(nickname)

    @validates("email")
    def validate_email(self, key, email):
        if email:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValueError("Provided email is not an email address")
            if User.query.filter(User.email == email).first():
                raise ValueError("Email is already in use")
            return html.escape(email)
        return None

    def set_password(self, password):
        """Set this User's password. It will create an argon2 hash from the specified string.

        Args:
            password (str): The password to create the hash from.

        Raises:
            ValueError: Password not provided
            ValueError: Password must be between 5 and 50 characters
        """
        if not password:
            raise ValueError("Password not provided")
        if len(password) < 4 or len(password) > 50:
            raise ValueError("Password must be between 4 and 50 characters")

        self.password_hash = argon2.using(rounds=8).hash(password)

    def check_password(self, password):
        """Check the user's password against the stored argon2 hash.

        Args:
            password (str): The password to check against

        Returns:
            bool: True if the password was correct, False if incorrect.
        """
        return argon2.verify(password, self.password_hash)

    def regen_api_key(self):
        """
        Regenerate this User's API key.
        """
        self.api_key = secrets.token_urlsafe(32)

    def save_to_db(self):
        """
        Save the Model to the database. It will automatically add a UserSettings model to this user if one has not been set already.
        """
        if self.settings is None:
            self.settings = UserSettings(
                avatar="/static/image/default.png",
            )
        db.session.add(self)
        db.session.commit()

    def get_id(self):
        """Flask-login function

        Returns:
            str: Secret login ID
        """
        return self.login_id

    @property
    def is_active(self):
        """Flask-login property

        Returns:
            bool: True if user is neither banned nor is_deleted
        """
        active = True
        if self.ban:
            if self.ban.has_expired:
                # their ban has expired, continue login
                self.ban = None
                db.session.commit()
            else:
                active = False
        if self.is_deleted:
            active = False
        return active

    def get_avatar(self, size: str = None) -> str:
        """Return the avatar for this user.

        Args:
            size (int, optional): The size to resize the avatar to. Does not work if the user has no avatar. Defaults to None.

        Returns:
            str: The avatar url
        """
        if not self.settings.avatar:
            return "/static/image/default.png"
        if size:
            return f"/{self.settings.avatar.split('/')[1]}/thumbnail/{self.settings.avatar.split('/')[-1]}?size={size}"
        return self.settings.avatar

    def has_role(self, role: UserRoles) -> bool:
        """Check if the user has a specific role or above.

        Args:
            role (UserRoles): The role to check for.

        Returns:
            bool: True if user has a role equal to or above the given role
        """
        return self.role.value >= role.value

    def has_permissions(
        self, permissions: Union[UserPermissions, List[UserPermissions]]
    ) -> bool:
        """Check if the user has the specified permissions

        Args:
            permissions (Union[UserPermissions, List[UserPermissions]]): The list of permissions or UserPermissions to check

        Returns:
            bool: True if the user has all of the permissions specified.
        """
        # Check if permissions are a list an iterate through them
        if isinstance(permissions, list):
            for p in permissions:
                if p not in self.permissions:
                    # User doesn't have these permissions
                    return False
        # Check for a single permission
        elif permissions not in self.permissions:
            return False
        return True

    def has_upvoted(self, post: Post) -> bool:
        """Check if a user has upvoted a post

        Args:
            post (Post): The post to check for an upvote on

        Returns:
            bool: True or false come on man
        """
        return bool(post.upvoters.filter_by(id=self.id).first())

    def has_downvoted(self, post: Post) -> bool:
        """Check if a user has downvoted a post

        Args:
            post (Post): The post to check for a downvote on

        Returns:
            bool: True or false come on man
        """
        return bool(post.downvoters.filter_by(id=self.id).first())

    def can_edit_post(self, post: Post) -> bool:
        """Check if a user has permissions to edit a post.

        Args:
            post (Post): The post to check.

        Returns:
            bool: True if user can edit, False if not.
        """
        return bool(
            (
                self.has_permissions(UserPermissions.EDIT_POSTS)
                or self.id == post.uploader.id
            )
        )

    @property
    def is_admin(self) -> bool:
        """Check if the user has admin permissions, for use in jinja templates

        Returns:
            bool: True or False
        """
        return self.has_role(UserRoles.ADMIN)

    @property
    def is_mod(self) -> bool:
        """Check if the user has moderator permissions, for use in jinja templates

        Returns:
            bool: True or False
        """
        return self.has_role(UserRoles.MODERATOR)

    @property
    def avatar_thumbnail(self) -> str:
        """Get the thumbnail for the avatar for this user

        Returns:
            str: The avatar url
        """
        return self.get_avatar(150)

    @property
    def profile_colour(self) -> str:
        return self.settings.profile_colour or "#4a4a4a"

    @property
    def profile_text_colour(self) -> str:
        return colour_contrast(self.profile_colour)

    def __repr__(self):
        return f"<User '{self.username}'>"
