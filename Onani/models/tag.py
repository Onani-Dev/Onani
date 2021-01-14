# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-12 21:05:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-13 21:33:32

import enum

from sqlalchemy_utils import ChoiceType

from . import db

alias_table = db.Table(
    "tag_aliases",
    db.Column("parent_id", db.Integer, db.ForeignKey("tags.id")),
    db.Column("child_id", db.Integer, db.ForeignKey("tags.id")),
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


class Tag(db.Model):
    """
    Tag Models
    """

    __tablename__ = "tags"

    # basic info
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    type = db.Column(
        ChoiceType(TagType, impl=db.Integer()),
        default=TagType.GENERAL,
        nullable=False,
    )

    # alias
    aliases = db.relationship(
        "Tag",
        secondary=alias_table,
        primaryjoin=(alias_table.c.parent_id == id),
        secondaryjoin=(alias_table.c.child_id == id),
        backref=db.backref("tags", lazy="dynamic"),
        lazy="dynamic",
    )

    def save_to_db(self):
        db.session.add(self)
        self.commit()

    def commit(self):
        db.session.commit()

    def __repr__(self):
        return "<Tag {0!r}>".format(self.__dict__)
