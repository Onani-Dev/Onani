# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 02:07:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-06 23:57:41

import datetime
import enum
from Onani.models.comment import PostComment

from Onani.models.file import File
from Onani.models.tag import Tag
from Onani.models.note import Note
from Onani.models.user import User
from sqlalchemy.orm import backref, validates
from sqlalchemy_utils import ChoiceType, JSONType, URLType

from . import db

post_upvotes = db.Table(
    "post_upvotes",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
)

post_downvotes = db.Table(
    "post_downvotes",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
)

post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
)

post_comments = db.Table(
    "post_comments",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("comment_id", db.Integer, db.ForeignKey("comments.id")),
)


class PostRating(enum.Enum):
    """
    Ratings for Post objects
    """

    SAFE = 1
    UNKNOWN = 2
    EXPLICIT = 3

    def __int__(self):
        return self.value


class PostStatus(enum.Enum):
    """
    Status for Post objects
    """

    DELETED = 0
    PENDING = 1
    ACCEPTED = 2

    def __int__(self):
        return self.value


class Post(db.Model):
    """
    Post object model
    """

    __tablename__ = "posts"

    # Basic stuff
    id = db.Column(db.Integer, primary_key=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(
        ChoiceType(PostStatus, impl=db.Integer()),
        default=PostStatus.PENDING,
        nullable=False,
    )
    rating = db.Column(
        ChoiceType(PostRating, impl=db.Integer()),
        default=PostRating.UNKNOWN,
        nullable=False,
    )
    source = db.Column(db.String)
    description = db.Column(db.String)

    # Foregin key shit
    file = db.relationship(File, uselist=False, backref="post_file")
    notes = db.relationship(Note, backref="post_notes", lazy=True)
    uploader = db.Column(db.Integer, db.ForeignKey("users.id"))

    tags = db.relationship(
        Tag,
        secondary=post_tags,
        primaryjoin=(post_tags.c.post_id == id),
        secondaryjoin=(post_tags.c.tag_id == id),
        backref=db.backref("post_tags", lazy="dynamic"),
        lazy="dynamic",
    )

    upvoters = db.relationship(
        User,
        secondary=post_upvotes,
        primaryjoin=(post_upvotes.c.post_id == id),
        secondaryjoin=(post_upvotes.c.user_id == id),
        backref=db.backref("post_upvoters", lazy="dynamic"),
        lazy="dynamic",
    )

    downvoters = db.relationship(
        User,
        secondary=post_downvotes,
        primaryjoin=(post_downvotes.c.post_id == id),
        secondaryjoin=(post_downvotes.c.user_id == id),
        backref=db.backref("post_downvoters", lazy="dynamic"),
        lazy="dynamic",
    )

    comments = db.relationship(
        PostComment,
        secondary=post_comments,
        primaryjoin=(post_comments.c.post_id == id),
        secondaryjoin=(post_comments.c.comment_id == id),
        backref=db.backref("post_comments", lazy="dynamic"),
        lazy="dynamic",
    )

    @property
    def score(self):
        return len(self.upvoters) - len(self.downvoters)

    def __repr__(self):
        return f"<Post {self.__dict__}>"
