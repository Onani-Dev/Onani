# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-17 02:37:00
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:16:58

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
    )

    expires: datetime.datetime = db.Column(db.DateTime(timezone=True), nullable=False)

    reason: str = db.Column(db.UnicodeText)

    @property
    def has_expired(self):
        return datetime.datetime.now(datetime.timezone.utc) >= self.expires

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Ban {self.__dict__}>"
