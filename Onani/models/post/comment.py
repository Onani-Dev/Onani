# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 23:34:00
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 12:28:10

from __future__ import annotations
import datetime
import html
from typing import TYPE_CHECKING

from sqlalchemy.orm import backref, validates

from . import db

if TYPE_CHECKING:
    from Onani.models.user import User


class PostComment(db.Model):
    """
    PostComment model
    """

    __tablename__ = "comments"

    # Comment id
    id: int = db.Column(db.Integer, primary_key=True)

    # The author's id
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Author user object
    author: User = db.relationship(
        "User", backref="posted_comments", lazy="joined", uselist=False
    )

    # The post relationship
    post_id: int = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    post = db.relationship("Post", lazy="joined", uselist=False, overlaps="comments")

    # The time that the comment was created
    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # The comment message content
    content: str = db.Column(db.UnicodeText, nullable=False)

    @validates("content")
    def validate_content(self, key, content):
        while "\n\n\n\n" in content:  # Max 3 consecutive newlines in a row
            content = content.replace("\n\n\n\n", "\n\n\n")
        if len(content.strip()) > 2000:
            raise ValueError("Comment was too long. (Over 2000 Chars)")

        return html.escape(content.strip())

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Comment {self.__dict__}>"
