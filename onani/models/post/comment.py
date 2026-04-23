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
    from onani.models.user import User


comment_upvotes = db.Table(
    "comment_upvotes",
    db.Column(
        "comment_id",
        db.Integer,
        db.ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.UniqueConstraint("comment_id", "user_id", name="uq_comment_upvotes_comment_user"),
)


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

    # Optional parent comment for threaded replies.
    parent_id: int = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True, index=True)

    parent = db.relationship(
        "PostComment",
        remote_side=[id],
        foreign_keys=[parent_id],
        uselist=False,
        backref=backref("replies", lazy="dynamic", cascade="all, delete-orphan"),
    )

    # The time that the comment was created
    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    # The comment message content
    content: str = db.Column(db.UnicodeText, nullable=False)

    # Cached cumulative comment upvotes.
    upvote_count: int = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    # Users who upvoted this comment.
    upvoters = db.relationship(
        "User",
        secondary=comment_upvotes,
        backref="comment_upvoters",
        lazy="dynamic",
    )

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
