# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 00:20:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-20 16:17:05

from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy.orm import validates

from . import db

if TYPE_CHECKING:
    from Onani.models.post.file import File


class Note(db.Model):
    """
    Note Model
    """

    __tablename__ = "notes"

    id: int = db.Column(db.Integer, primary_key=True)

    file_id: int = db.Column(db.Integer, db.ForeignKey("files.id"), nullable=False)
    file: File = db.relationship(
        "File", backref="file_notes", lazy="joined", uselist=False, viewonly=True
    )

    text: str = db.Column(db.String)

    x: int = db.Column(db.Integer)
    """Horizontal offset from the top left corner"""

    y: int = db.Column(db.Integer)
    """Vertical offset from the top left corner"""

    width: int = db.Column(db.Integer)
    """Width (from left to right)"""

    height: int = db.Column(db.Integer)
    """Height (from top to bottom)"""

    @validates("x", "y")
    def validate_xy(self, key, value):
        if value < 0:
            raise ValueError(f"{key} can't be negative")
        return value

    @validates("width")
    def validate_width(self, key, width):
        if width <= 0:
            raise ValueError("width can't be negative or null")
        if self.file.width < (self.x + width):
            width = self.file.width - self.x
        return width

    @validates("height")
    def validate_height(self, key, height):
        if height <= 0:
            raise ValueError("height can't be negative or null")
        if self.file.height < (self.y + height):
            height = self.file.height - self.y
        return height

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<Note {self.__dict__}>"
