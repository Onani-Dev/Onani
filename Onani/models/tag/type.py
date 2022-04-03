# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-22 00:00:24
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-22 00:47:21
import enum


class TagType(enum.Enum):
    """
    Types for Tag Objects
    Can be: BANNED, ARTIST, CHARACTER, COPYRIGHT, GENERAL, META
    """

    BANNED = 0
    GENERAL = 1
    ARTIST = 2
    CHARACTER = 3
    COPYRIGHT = 4
    META = 5

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}
