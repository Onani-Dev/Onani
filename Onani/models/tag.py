# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-12 21:05:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-10 19:49:05

import enum

from sqlalchemy_utils import ChoiceType

from . import db


post_table = db.Table(
    "tag_posts",
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
)


class TagType(enum.Enum):
    """
    Types for Tag Objects
    Can be: ARTIST, CHARACTER, COPYRIGHT, GENERAL, META
    """

    BANNED = 0
    GENERAL = 1
    ARTIST = 2
    CHARACTER = 3
    COPYRIGHT = 4
    META = 5

    def __int__(self):
        return self.value

    @classmethod
    def get_all(self):
        return {e.name: e.value for e in self}


class Tag(db.Model):
    """
    Tag Models
    """

    __tablename__ = "tags"

    # The tags primary key.
    id = db.Column(db.Integer, primary_key=True)

    # The tag's name. must be unique
    name = db.Column(db.String, nullable=False, index=True, unique=True)

    # The tag's type. enum. sick.
    type = db.Column(
        ChoiceType(TagType, impl=db.Integer()),
        default=TagType.GENERAL,
        nullable=False,
    )

    # Tag's description. will be used for users to see what the tag is about.
    description = db.Column(
        db.String, default="No description has been added to this tag."
    )

    # If this tag is an Alias of another tag this value will be that tag's ID
    alias_of = db.Column(db.Integer, db.ForeignKey("tags.id"))

    # If this tag has aliases they will be listed here.
    aliases = db.relationship(
        "Tag", backref=db.backref("tag_aliases", remote_side=[id], lazy="joined")
    )

    # the posts with this tag will be here.
    posts = db.relationship(
        "Post", secondary=post_table, backref="tag_posts", lazy="dynamic"
    )

    # The post count for this tag's posts
    post_count = db.Column(db.Integer, nullable=False, default=0)

    # The url that will be associated with this tag. only used for artists.
    url = db.Column(db.String)

    @property
    def is_alias(self):
        return bool(self.alias_of)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Tag {self.__dict__}>"
