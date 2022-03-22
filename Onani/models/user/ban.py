# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-17 02:37:00
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-22 18:58:57

import datetime

from . import db


class Ban(db.Model):
    """
    Ban model
    """

    __tablename__ = "bans"

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("users.id"))
    since = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    expires = db.Column(db.DateTime(timezone=True), nullable=False)
    reason = db.Column(db.UnicodeText)

    @property
    def has_expired(self):
        return datetime.datetime.now(datetime.timezone.utc) >= self.expires

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Ban {self.__dict__}>"
