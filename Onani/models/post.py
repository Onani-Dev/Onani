# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 02:07:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-14 00:17:53

import datetime
import enum

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

    QUESTIONABLE = 1
    SAFE = 2
    EXPLICIT = 3

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}

    @classmethod
    def choices(self):
        return [(choice, choice.name) for choice in self]

    @classmethod
    def coerce(self, item):
        return self(int(item)) if not isinstance(item, self) else item

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)


class PostStatus(enum.Enum):
    """
    Status for Post objects
    """

    DELETED = 0
    ACTIVE = 1

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}

    @classmethod
    def choices(self):
        return [(choice, choice.name) for choice in self]

    @classmethod
    def coerce(self, item):
        return self(int(item)) if not isinstance(item, self) else item

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)


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
        default=PostRating.QUESTIONABLE,
        nullable=False,
    )

    # The post's source. will be a url.
    source = db.Column(db.String)

    # the post's description
    description = db.Column(db.String)

    # The post's file(s). has information on file sizes etc
    files = db.relationship("File", backref="post_files", lazy="joined")

    # The post's notes. those little thingys on the image over the japanese text :)
    notes = db.relationship("Note", backref="post_notes", lazy="joined")

    # The post's uploader. is a user.
    uploader = db.Column(db.Integer, db.ForeignKey("users.id"))

    # The post's tags. will be a list of tags that can be appended to.
    tags = db.relationship("Tag", secondary=post_tags, backref="posts", lazy="joined")

    # Post's upvoters. users. contributes to the post's rating/score
    upvoters = db.relationship(
        "User", secondary=post_upvotes, backref="post_upvoters", lazy="dynamic"
    )

    # Post's downvoters. users. contributes to the post's rating/score (reddit moment)
    downvoters = db.relationship(
        "User", secondary=post_downvotes, backref="post_downvoters", lazy="dynamic"
    )

    # The post's comments. will be filtered for naughty words or other bad things.
    comments = db.relationship(
        "PostComment", secondary=post_comments, backref="post_comments", lazy="dynamic"
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
