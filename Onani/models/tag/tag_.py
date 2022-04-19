# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-12 21:05:15
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 13:01:33

from __future__ import annotations
from email.policy import default
import enum
from typing import List

from sqlalchemy_utils import ChoiceType

from . import TagType, db


class Tag(db.Model):
    """
    Tag Models
    """

    __tablename__ = "tags"

    # The tags primary key.
    id: int = db.Column(db.Integer, primary_key=True)

    # The tag's name. must be unique
    name: str = db.Column(db.String, nullable=False, index=True, unique=True)

    # The tag's type. enum. sick.
    type: TagType = db.Column(
        ChoiceType(TagType, impl=db.Integer()),
        default=TagType.GENERAL,
        nullable=False,
    )

    # Tag's description. will be used for users to see what the tag is about.
    description: str = db.Column(
        db.String, default="No description has been added to this tag."
    )

    # If a post has this tag, automatically mark as explicit.
    explicit: bool = db.Column(db.Boolean, default=False)

    # If a post has a restricted tag, it will only be available to premium and above
    restricted: bool = db.Column(db.Boolean, default=False)

    # If this tag is an Alias of another tag this value will be that tag's ID
    alias_of: int = db.Column(db.Integer, db.ForeignKey("tags.id"))

    # If this tag has aliases they will be listed here.
    aliases: List[Tag] = db.relationship(
        "Tag", backref=db.backref("tag_aliases", remote_side=[id], lazy="joined")
    )

    # The post count for this tag's posts
    post_count: int = db.Column(db.Integer, default=0)

    # The url that will be associated with this tag. only used for artists.
    url: str = db.Column(db.String)

    @property
    def is_alias(self) -> bool:
        return bool(self.alias_of)

    @property
    def humanize(self) -> str:
        return self.name.replace("_", " ").capitalize()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Tag {self.__dict__}>"
