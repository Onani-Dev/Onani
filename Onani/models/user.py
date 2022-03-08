# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 23:57:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 02:24:52

import datetime
import enum
import html
import secrets

import regex as re
from flask_login import UserMixin
from Onani.models.ban import Ban
from Onani.models.tag import Tag
from passlib.hash import argon2
from sqlalchemy.orm import backref, validates
from sqlalchemy_utils import ChoiceType, JSONType, URLType

from . import db

tag_blacklist = db.Table(
    "tag_blacklist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)


class UserPermissions(enum.Enum):
    """
    Permissions for User models.
    """

    MEMBER = 1
    ARTIST = 2
    PREMIUM = 3
    HELPER = 4
    MODERATOR = 5
    ADMIN = 6
    OWNER = 666

    def __int__(self):
        return self.value


class UserSettings(db.Model):
    """
    UserSettings Models
    """

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("users.id"))

    # User biography. allows custom text on the profile. (and hopefully not Cross Site Scripting)
    biography = db.Column(db.UnicodeText)

    # The link to the user's avatar.
    avatar = db.Column(db.String)

    # The user's custom css. overrides the default css that i worked so hard on :(
    custom_css = db.Column(db.UnicodeText)

    # The user's connections to other website's accounts
    connections = db.Column(
        db.JSON,
        default={
            "deviantart": None,
            "discord": None,
            "github": None,
            "patreon": None,
            "pixiv": None,
            "twitter": None,
        },
    )

    @validates("biography")
    def validate_biography(self, key, biography):
        if len(biography) > 1024:
            raise AssertionError("Biography is too large. (Max 1024)")
        return html.escape(biography)


class User(UserMixin, db.Model):
    """
    User Models
    """

    __tablename__ = "users"

    # Users ID, obviously unique as it is the primary key
    id = db.Column(db.Integer, primary_key=True)

    # Users username, must be unique
    username = db.Column(db.String, index=True, unique=True, nullable=False)

    # Users email, optional and must be unique
    email = db.Column(db.String, index=True, unique=True)

    # The argon2 hash of the users password.
    password_hash = db.Column(db.String, nullable=False)

    # The time this user was created. it doesn't need to be touched.
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # The User's permissions. this affects what the user can do.
    permissions = db.Column(
        ChoiceType(UserPermissions, impl=db.Integer()),
        default=UserPermissions.MEMBER,
        nullable=False,
    )

    # The api key the user will use for the /api endpoint. Grants full control over the user account
    api_key = db.Column(
        db.String,
        index=True,
        unique=True,
        default=lambda: secrets.token_urlsafe(32),
    )

    # The ban that this user has. will be None if not banned.
    ban = db.relationship(Ban, uselist=False, backref="user_ban")

    # The tag blacklist. posts with tags on this list will not appear on this user's results.
    tag_blacklist = db.relationship(
        "Tag",
        secondary=tag_blacklist,
        backref="user_blacklist",
        lazy="dynamic",
    )

    # The user's settings. eg. custom css or profile connections
    settings = db.relationship("UserSettings", uselist=False, backref="user_settings")

    # The users comments on posts.
    comments = db.relationship("PostComment", backref="user_comments", lazy="dynamic")

    # The users uploaded posts.
    posts = db.relationship("Post", backref="user_posts", lazy="dynamic")

    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise AssertionError("No username provided")
        if len(username) < 3 or len(username) > 32:
            raise AssertionError("Username must be between 3 and 32 characters")
        if User.query.filter(User.username == username).first():
            raise AssertionError("Username is already in use")
        return username

    @validates("email")
    def validate_email(self, key, email):
        if email is not None:
            if not re.match("[^@]+@[^@]+\.[^@]+", email):
                raise AssertionError("Provided email is not an email address")
            if User.query.filter(User.email == email).first():
                raise AssertionError("Email is already in use")
        return email

    @property
    def is_banned(self):
        """Check if this user is banned.

        Returns:
            bool: True if this user is banned and False if not.
        """
        return self.ban is not None

    def set_password(self, password):
        """Set this User's password. It will create an argon2 hash from the specified string.

        Args:
            password (str): The password to create the hash from.

        Raises:
            ValueError: Password not provided
            ValueError: Password must contain 1 capital letter and 1 number
            ValueError: Password must be between 5 and 50 characters
        """
        if not password:
            raise ValueError("Password not provided")
        if not re.match("\d.*[A-Z]|[A-Z].*\d", password):
            raise ValueError("Password must contain 1 capital letter and 1 number")
        if len(password) < 5 or len(password) > 50:
            raise ValueError("Password must be between 5 and 50 characters")

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
        self.commit()

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

    def __repr__(self):
        return f"<User {self.__dict__}>"
