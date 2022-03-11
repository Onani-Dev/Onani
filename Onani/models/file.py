# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:33:12
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 03:27:28
from . import db


class File(db.Model):
    """
    File model
    """

    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"))
    url = db.Column(db.String)
    hash = db.Column(db.String)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    filesize = db.Column(db.Integer)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<File {self.__dict__}>"
