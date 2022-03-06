# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:20:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-06 20:18:03
from . import db


class Note(db.Model):
    """
    Note Model
    """

    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    text = db.Column(db.String)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Note {0!r}>".format(self.__dict__)
