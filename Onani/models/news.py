# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-05 01:33:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 01:56:42
import datetime
import html

from sqlalchemy.orm import validates

from . import db


class NewsPost(db.Model):
    """
    NewsPost model
    """

    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)

    @validates("title")
    def validate_title(self, key, title):
        return html.escape(title)

    @validates("content")
    def validate_content(self, key, content):
        return html.escape(content)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<NewsPost {self.__dict__}>"
