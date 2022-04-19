# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-05 01:33:34
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 11:55:04
import datetime
import html

from sqlalchemy.orm import validates
from sqlalchemy_utils import ChoiceType

from Onani.models.user.user_ import User

from . import NewsType, db


class NewsPost(db.Model):
    """
    NewsPost model
    """

    __tablename__ = "news"

    id: int = db.Column(db.Integer, primary_key=True)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author: User = db.relationship("User", backref="user_news")
    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    title: str = db.Column(db.String, nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)

    type: NewsType = db.Column(
        ChoiceType(NewsType, impl=db.Integer()),
        default=NewsType.ANNOUNCEMENT,
        nullable=False,
    )

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
