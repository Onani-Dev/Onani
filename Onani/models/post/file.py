# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:33:12
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-22 00:47:50
import os

from sqlalchemy.orm import validates

from . import db


class File(db.Model):
    """
    File model
    """

    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"))
    url = db.Column(db.String, unique=True)
    hash = db.Column(db.String, unique=True, index=True)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    filesize = db.Column(db.Integer)

    @validates("hash")
    def validate_hash(self, key, hash_):
        if hash_:
            if File.query.filter(File.hash == hash_).first():
                raise ValueError("File already exists.")
            return hash_
        return None

    def delete(self):
        """Delete this file from the database and the disk.

        Raises:
            Exception: The file couldn't be deleted.
        """
        os.remove(self.url)
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<File {self.__dict__}>"
