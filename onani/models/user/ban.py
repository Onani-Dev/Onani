# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-17 02:37:00
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-24 14:11:23

import datetime

from . import db


class Ban(db.Model):
    """
    Ban model
    """

    __tablename__ = "bans"

    id: int = db.Column(db.Integer, primary_key=True)

    user: int = db.Column(db.Integer, db.ForeignKey("users.id"))

    since: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    expires: datetime.datetime = db.Column(db.DateTime(timezone=True))

    reason: str = db.Column(db.UnicodeText)

    posts_hidden: bool = db.Column(db.Boolean, default=False)

    posts_deleted: bool = db.Column(db.Boolean, default=False)

    @property
    def has_expired(self):
        if not self.expires:
            return False
        now = datetime.datetime.now(datetime.timezone.utc)
        expires = self.expires
        # SQLite returns naive datetimes; treat them as UTC
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=datetime.timezone.utc)
        return now >= expires

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Ban {self.__dict__}>"
