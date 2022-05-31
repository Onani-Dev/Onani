# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-04 01:02:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:08:33
import datetime
from sqlalchemy.orm.query import Query
from sqlalchemy_utils import ChoiceType

from . import CollectionStatus, db

collection_posts = db.Table(
    "collection_posts",
    db.Column("collection_id", db.Integer, db.ForeignKey("collections.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
)


class Collection(db.Model):
    """
    Collection Models
    """

    __tablename__ = "collections"

    id: int = db.Column(db.Integer, primary_key=True)

    title: str = db.Column(db.String, nullable=False, index=True)

    description: str = db.Column(
        db.String, default="No description has been added to this collection."
    )

    posts: Query = db.relationship(
        "Post",
        secondary=collection_posts,
        backref="collection_posts",
        lazy="dynamic",
    )

    status: CollectionStatus = db.Column(
        ChoiceType(CollectionStatus, impl=db.Integer()),
        default=CollectionStatus.PENDING,
        nullable=False,
    )

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    creator: int = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return "<Collection {0!r}>".format(self.__dict__)
