# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-04 01:02:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-04 16:00:36
import datetime
import enum

from sqlalchemy_utils import ChoiceType

from . import db

collection_table = db.Table(
    "collection_posts",
    db.Column("collection_id", db.Integer, db.ForeignKey("collections.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
)


class CollectionStatus(enum.Enum):
    """
    Status for collections
    """

    BANNED = 0
    PENDING = 1
    ACCEPTED = 2

    def __int__(self):
        return self.value


class Collection(db.Model):
    """
    Collection Models
    """

    __tablename__ = "collections"

    # basic info
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False, index=True)
    description = db.Column(
        db.String(2048), default="No description has been added to this collection."
    )

    posts = db.relationship(
        "Post",
        secondary=collection_table,
        backref=db.backref("collection", lazy="dynamic"),
    )
    status = db.Column(
        ChoiceType(CollectionStatus, impl=db.Integer()),
        default=CollectionStatus.PENDING,
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    creator = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return "<Collection {0!r}>".format(self.__dict__)
