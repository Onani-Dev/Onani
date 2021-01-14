# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-14 21:33:13

from ..utils import setup_logger

log = setup_logger(__name__)


class Commentary(object):
    """
    Commentary for Posts
    """

    __slots__ = ("_db", "_original", "_translated")

    def __init__(self, db, original: str = None, translated: str = None):
        self._db = db
        self._original = original
        self._translated = translated

    @property
    def original(self) -> str:
        return self._original

    @original.setter
    def original(self, value: str) -> None:
        # database shit
        self._original = value

    @property
    def translated(self) -> str:
        return self._translated

    @translated.setter
    def translated(self, value: str) -> None:
        # database shit
        self._translated = value

    def to_dict(self):
        return {"original": self.original, "translated": self.translated}
