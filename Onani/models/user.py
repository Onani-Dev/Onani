# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 23:57:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-17 03:03:24

import datetime
import enum
import html
import secrets

import regex as re
from flask_login import UserMixin
from passlib.hash import argon2
from sqlalchemy.orm import backref, validates
from sqlalchemy_utils import ChoiceType, URLType, JSONType

from . import db

tag_blacklist = db.Table(
    "tag_blacklist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)


class UserPermissions(enum.Enum):
    """
    Permissions for User objects.
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

    ban = db.relationship("Ban", uselist=False, backref="user_ban")
    # Ban info
    # is_banned = db.Column(db.Boolean, default=False, nullable=False)
    # ban_expires = db.Column(db.DateTime)
    # ban_reason = db.Column(db.UnicodeText)

    # User preferences
    tag_blacklist = db.relationship(
        "Tag",
        secondary=tag_blacklist,
        backref=db.backref("user_tag_blacklist", lazy="dynamic"),
    )
    custom_css = db.Column(db.UnicodeText)

    # User Profile
    biography = db.Column(db.UnicodeText(1024))
    avatar = db.Column(db.String(256))

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
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<User {0!r}>".format(self.__dict__)
