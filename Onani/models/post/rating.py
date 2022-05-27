# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:07:34
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 22:24:13
from enum import Enum, auto


class PostRating(Enum):
    """
    Ratings for Post objects
    """

    # TODO: CHANGE THIS TO CHARACTERS!!!
    SAFE = 0
    QUESTIONABLE = 1
    EXPLICIT = 2

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return item if isinstance(item, cls) else cls(int(item))

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)
