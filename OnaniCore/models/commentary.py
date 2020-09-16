# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-03 19:24:16

from ..utils import setup_logger

log = setup_logger(__name__)


class Commentary(object):
    """
    Commentary for Posts
    """

    __slots__ = ("_db", "original", "translated")

    def __init__(self, db, original: str = None, translated: str = None):
        self._db
        self.original = original
        self.translated = translated

    def edit_original(self, new_string: str):
        # TODO #18
        pass

    def edit_translated(self, new_string: str):
        # TODO #18
        pass

    def to_dict(self):
        return {x: getattr(self, x) for x in self.__slots__ if x != "_db"}
