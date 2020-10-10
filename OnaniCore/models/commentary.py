# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-17 20:04:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-11 02:15:40

from ..utils import setup_logger

log = setup_logger(__name__)


class Commentary(object):
    """
    Commentary for Posts
    """

    __slots__ = ("_db", "original", "translated")

    def __init__(self, db, original: str = None, translated: str = None):
        self._db = db
        self.original = original
        self.translated = translated

    def edit_original(self, new_string: str):
        # TODO #18
        pass

    def edit_translated(self, new_string: str):
        # TODO #18
        pass

    def to_dict(self):
        return {"original": self.original, "translated": self.translated}
