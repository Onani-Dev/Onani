# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-12 21:05:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 15:06:59

from __future__ import annotations

from typing import List

from sqlalchemy import func
from sqlalchemy.orm import validates
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

    # ARTIST ONLY
    # The url that will be associated with this tag. only used for artists.
    url: str = db.Column(db.String)

    # user relationship for the artist if they are registered on Onani
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"))

    @validates("url", "user", "user_id")
    def validate_artist_tag(self, key, value):
        # ARTISTS ONLY!!!!!
        return None if self.type != TagType.ARTIST else value

    @property
    def is_alias(self) -> bool:
        """Property to check if the tag is an alias or not

        Returns:
            bool
        """
        return bool(self.alias_of)

    @property
    def humanized(self) -> str:
        """Return a humanized version of the tag's name

        Returns:
            str: The humanized string (name)
        """
        return self.name.replace("_", " ")  # .capitalize()

    @property
    def text_format(self) -> str:
        """Return a string for the Tag used in user specifying tag types.

        Returns:
            str: The string
        """
        return (
            f"{self.type.name.lower()}:{self.name}"
            if self.type != TagType.GENERAL
            else self.name
        )

    def recount_posts(self):
        self.post_count = len(self.posts)
        # self.post_count = self.posts.with_entities(func.count()).scalar()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Tag {self.__dict__}>"
