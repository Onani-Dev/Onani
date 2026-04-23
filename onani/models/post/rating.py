# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:07:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-04 16:04:22
from enum import Enum, auto
from functools import cache


class PostRating(str, Enum):
    """
    Ratings for Post objects
    """

    GENERAL = "g"
    QUESTIONABLE = "q"
    SENSITIVE = "s"
    EXPLICIT = "e"

    @classmethod
    @cache
    def get_all(cls):
        return {e.name: e for e in cls}

    @classmethod
    @cache
    def choices(cls):
        return [(choice, choice.name.capitalize()) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return item if isinstance(item, cls) else cls(str(item))

    def __str__(self):
        return self.value
