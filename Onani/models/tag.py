# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-12 21:05:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-06 20:19:11

from email.policy import default
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


class Tag(db.Model):
    """
    Tag Models
    """

    __tablename__ = "tags"

    # basic info
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, index=True)
    type = db.Column(
        ChoiceType(TagType, impl=db.Integer()),
        default=TagType.GENERAL,
        nullable=False,
    )
    description = db.Column(
        db.String, default="No description has been added to this tag."
    )

    # alias
    alias_of = db.Column(db.Integer, db.ForeignKey("tags.id"))
    aliases = db.relationship(
        "Tag", backref=db.backref("tag", remote_side=[id], lazy="joined")
    )

    # list posts
    posts = db.relationship(
        "Post", secondary=post_table, backref=db.backref("tag", lazy="dynamic")
    )

    post_count = db.Column(db.Integer, nullable=False, default=0)

    @property
    def is_alias(self):
        return bool(self.alias_of)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Tag {0!r}>".format(self.__dict__)


# aliases = db.relationship(
#     "Tag",
#     secondary=tag_aliases,
#     primaryjoin=(tag_aliases.c.parent_id == id),
#     secondaryjoin=(tag_aliases.c.child_id == id),
#     backref=db.backref("tags", lazy="dynamic"),
#     lazy="dynamic",
# )
