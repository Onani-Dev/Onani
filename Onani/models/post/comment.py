# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 23:34:00
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-01 00:14:31
import datetime
import html

from Onani.models.user import User
from sqlalchemy.orm import backref, validates

from . import db


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
        "User", backref="post_comments", lazy="joined", uselist=False
    )

    # The post relationship
    post_id: int = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    # The time that the comment was created
    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # The comment message content
    content: str = db.Column(db.UnicodeText, nullable=False)

    @validates("content")
    def validate_content(self, key, content):
        if len(content) > 2000:
            raise ValueError("Comment was too long. (Over 2000 Chars)")

        return html.escape(content)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Comment {self.__dict__}>"
