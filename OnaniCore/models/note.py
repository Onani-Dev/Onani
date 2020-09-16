# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-03 19:20:13

from ..utils import setup_logger

log = setup_logger(__name__)


class Note(object):
    """
    Notes for Posts
    """

    __slots__ = ("_db", "x", "y", "width", "height", "content")

    def __init__(
        self,
        db,
        x: int = None,
        y: int = None,
        width: int = None,
        height: int = None,
        content: str = None,
    ):
        self._db = db
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.content = content

    # TODO #19

    def to_dict(self):
        return {x: getattr(self, x) for x in self.__slots__ if x != "_db"}
