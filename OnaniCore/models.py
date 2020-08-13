# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-13 18:11:40
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-13 18:25:48
import logging

log = logging.getLogger(__name__)


class Tag:
    """
    Onani Tag Object
    """

    def __init__(self, tag_string: str, db):
        self._db = db
        self.tag_string = tag_string
        self.raw = self._db.get_raw_tag_info(self.tag_string)
        self.type = self.raw.get("type")
        self.is_deleted = self.raw.get("is_deleted")
        self.is_banned = self.raw.get("is_banned")
        self.aliases = self.raw.get("aliases")
