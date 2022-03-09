# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 02:07:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 15:44:21

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
    ACTIVE = 1

    def __int__(self):
        return self.value


class Post(db.Model):
    """
    Post object model
    """

    __tablename__ = "posts"

    # The post primary key
    id = db.Column(db.Integer, primary_key=True)

    # The time the post was created.
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # The status of the post. if it is deleted for any reason it will become PostStatus.DELETED
    status = db.Column(
        ChoiceType(PostStatus, impl=db.Integer()),
        default=PostStatus.ACTIVE,
        nullable=False,
    )

    # The explicitness rating of a post. will be manually set by uploader and can be changed by an admin or moderator.
    rating = db.Column(
        ChoiceType(PostRating, impl=db.Integer()),
        default=PostRating.UNKNOWN,
        nullable=False,
    )

    # The post's source. will be a url.
    source = db.Column(db.String)

    # the post's description
    description = db.Column(db.String)

    # The post's file. has information on filesize etc
    file = db.relationship(File, uselist=False, backref="post_file")

    # The post's notes. those little thingys on the image over the japanese text :)
    notes = db.relationship(Note, backref="post_notes", lazy="joined")

    # The post's uploader. is a user.
    uploader = db.Column(db.Integer, db.ForeignKey("users.id"))

    # The post's tags. will be a list of tags that can be appended to.
    tags = db.relationship(
        Tag,
        secondary=post_tags,
        primaryjoin=(post_tags.c.post_id == id),
        secondaryjoin=(post_tags.c.tag_id == id),
        backref="post_tags",
        lazy="dynamic",
    )

    # Post's upvoters. users. contributes to the post's rating/score
    upvoters = db.relationship(
        User,
        secondary=post_upvotes,
        primaryjoin=(post_upvotes.c.post_id == id),
        secondaryjoin=(post_upvotes.c.user_id == id),
        backref="post_upvoters",
        lazy="dynamic",
    )

    # Post's downvoters. users. contributes to the post's rating/score (reddit moment)
    downvoters = db.relationship(
        User,
        secondary=post_downvotes,
        primaryjoin=(post_downvotes.c.post_id == id),
        secondaryjoin=(post_downvotes.c.user_id == id),
        backref="post_downvoters",
        lazy="dynamic",
    )

    # The post's comments. will be filtered for naughty words or other bad things.
    comments = db.relationship(
        PostComment,
        secondary=post_comments,
        primaryjoin=(post_comments.c.post_id == id),
        secondaryjoin=(post_comments.c.comment_id == id),
        backref="post_comments",
        lazy="dynamic",
    )

    @property
    def score(self) -> int:
        """Get the rating score of this post.

        Returns:
            int: The Score.
        """
        return len(self.upvoters) - len(self.downvoters)

    def __repr__(self):
        return f"<Post {self.__dict__}>"
