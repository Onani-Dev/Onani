# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 23:57:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-04 02:59:21

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

    # User Profile
    biography = db.Column(db.UnicodeText(1024))
    avatar = db.Column(db.String(256))
    custom_css = db.Column(db.UnicodeText)
    deviantart = db.Column(db.String(128))
    discord = db.Column(db.String(128))
    github = db.Column(db.String(128))
    patreon = db.Column(db.String(128))
    pixiv = db.Column(db.String(128))
    twitter = db.Column(db.String(128))


class User(UserMixin, db.Model):
    """
    User Models
    """

    __tablename__ = "users"

    # Core user stuff
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True, nullable=False)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    permissions = db.Column(
        ChoiceType(UserPermissions, impl=db.Integer()),
        default=UserPermissions.MEMBER,
        nullable=False,
    )
    api_key = db.Column(
        db.String(64),
        index=True,
        unique=True,
        default=lambda: secrets.token_urlsafe(32),
    )

    ban = db.relationship(Ban, uselist=False, backref="user_ban")

    # User preferences
    tag_blacklist = db.relationship(
        Tag,
        secondary=tag_blacklist,
        backref=db.backref("user_tag_blacklist", lazy="dynamic"),
    )
    settings = db.relationship(UserSettings, uselist=False, backref="user_settings")

    @validates("username")
    def validate_username(self, key, username):
        if not username:
            raise AssertionError("No username provided")
        if User.query.filter(User.username == username).first():
            raise AssertionError("Username is already in use")
        if len(username) < 3 or len(username) > 32:
            raise AssertionError("Username must be between 3 and 32 characters")
        return username

    @validates("email")
    def validate_email(self, key, email):
        if not email:
            raise AssertionError("No email provided")
        if User.query.filter(User.email == email).first():
            raise AssertionError("Email is already in use")
        if not re.match("[^@]+@[^@]+\.[^@]+", email):
            raise AssertionError("Provided email is not an email address")
        return email

    @validates("biography")
    def validate_biography(self, key, biography):
        if len(biography) > 512:
            raise AssertionError("Biography is too large. (Max 512)")
        return html.escape(biography)

    @property
    def is_banned(self):
        return False if self.ban is None else True

    def set_password(self, password):
        if not password:
            raise AssertionError("Password not provided")
        if not re.match("\d.*[A-Z]|[A-Z].*\d", password):
            raise AssertionError("Password must contain 1 capital letter and 1 number")
        if len(password) < 5 or len(password) > 50:
            raise AssertionError("Password must be between 5 and 50 characters")

        self.password_hash = argon2.using(rounds=8).hash(password)

    def check_password(self, password):
        return argon2.verify(password, self.password_hash)

    def regen_api_key(self):
        self.api_key = secrets.token_urlsafe(32)
        self.commit()

    def save_to_db(self):
        self.settings = UserSettings(
            avatar="/image/default.png",
        )
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<User {0!r}>".format(self.__dict__)
