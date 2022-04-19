# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:33:12
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 14:29:53

from __future__ import annotations
import os
from typing import TYPE_CHECKING

from sqlalchemy.orm import validates

from . import db

if TYPE_CHECKING:
    from Onani.models.post.note import Note


class File(db.Model):
    """
    File model
    """

    __tablename__ = "files"

    id: int = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.Integer, db.ForeignKey("posts.id"))
    url: str = db.Column(db.String, unique=True)
    sha256_hash: str = db.Column(db.String, unique=True, index=True)
    md5_hash: str = db.Column(db.String, index=True)
    width: int = db.Column(db.Integer)
    height: int = db.Column(db.Integer)
    filesize: int = db.Column(db.Integer)

    # The file's notes. those little thingys on the image over the japanese text :)
    notes: Note = db.relationship(
        "Note", backref="file_notes", lazy="joined"
    )

    @validates("sha256_hash")
    def validate_hash(self, key, hash_):
        if hash_:
            if File.query.filter(File.sha256_hash == hash_).first():
                raise ValueError("File already exists.")
            return hash_
        return None

    def thumbnail(self, size: int = 150) -> str:
        return f"/thumbnail/{size}x{size}{self.url}"

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
