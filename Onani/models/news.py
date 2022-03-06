# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-05 01:33:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-06 20:17:59
import datetime
from . import db


class NewsPost(db.Model):
    """
    NewsPost model
    """

    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    title = db.Column(db.String, nullable=False, index=True)
    content = db.Column(db.UnicodeText, nullable=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<NewsPost {0!r}>".format(self.__dict__)
