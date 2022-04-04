# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 23:57:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-05 00:12:31

import datetime
import html
import secrets
import uuid

import regex as re
from flask_login import UserMixin
from passlib.hash import argon2
from sqlalchemy.orm import validates
from sqlalchemy_utils import ChoiceType

from . import Ban, db
from .roles import UserRoles
from .settings import UserSettings

tag_blacklist = db.Table(
    "tag_blacklist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)


class User(UserMixin, db.Model):
    """
    User Models
    """

    __tablename__ = "users"

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.settings:
            self.settings = UserSettings()

    # Users ID, obviously unique as it is the primary key
    id = db.Column(db.Integer, primary_key=True)

    # Users username, must be unique
    username = db.Column(db.String, index=True, unique=True, nullable=False)

    # Users email, optional and must be unique
    email = db.Column(db.String, index=True, unique=True)

    # The argon2 hash of the users password.
    password_hash = db.Column(db.String, nullable=False)

    # The time this user was created. it doesn't need to be touched.
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # The User's role. this affects what the user can do.
    role = db.Column(
        ChoiceType(UserRoles, impl=db.Integer()),
        default=UserRoles.MEMBER,
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
    comments = db.relationship(
        "PostComment", backref="user_comments", lazy="dynamic", viewonly=True
    )

    # The users uploaded posts.
    posts = db.relationship("Post", backref="user_posts", lazy="dynamic", viewonly=True)

    # Amount of posts this user has uploaded.
    post_count = db.Column(db.Integer, default=0, nullable=False)

    # ULTRA SECRET LOGIN UUID FOR INTERNAL LOGGING IN!!!!1!!!1 (hidden value for securely logging in users with flask-login)
    login_id = db.Column(
        db.String, index=True, unique=True, default=lambda: str(uuid.uuid4())
    )

    # If the user deletes their account, this will become true.
    is_deleted = db.Column(db.Boolean, default=False)

    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise ValueError("No username provided")
        if len(username) < 3 or len(username) > 32:
            raise ValueError("Username must be between 3 and 32 characters")
        if User.query.filter(User.username == username).first():
            raise ValueError("Username is already in use")
        return html.escape(username)

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

    def get_avatar(self, size: int = None) -> str:
        """Return the avatar for this user.

        Args:
            size (int, optional): The size to resize the avatar to. Does not work if the user has no avatar. Defaults to None.

        Returns:
            str: The avatar url
        """
        if not self.settings.avatar:
            return "/static/image/default.png"
        if size:
            return f"/thumbnail/{size}x{size}{self.settings.avatar}"
        return self.settings.avatar

    @property
    def avatar_thumbnail(self):
        return self.get_avatar(150)

    @property
    def profile_colour(self):
        return self.settings.profile_colour or "#4a4a4a"

    def __repr__(self):
        return f"<User {self.username}>"
