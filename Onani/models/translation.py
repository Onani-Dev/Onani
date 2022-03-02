# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:20:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-03 00:46:12
from . import db


class Translation(db.Model):
    """
    Translation model
    """

    __tablename__ = "translations"

    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    text = db.Column(db.String(1024))
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Translation {0!r}>".format(self.__dict__)
