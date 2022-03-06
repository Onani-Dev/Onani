# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 23:34:00
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 00:28:47
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

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    content = db.Column(db.UnicodeText, nullable=False)

    @validates("content")
    def validate_content(self, key, content):
        if len(content) > 500:
            raise AssertionError("Comment was too long. (Over 500 Chars)")

        return html.escape(content)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Comment {self.__dict__}>"
