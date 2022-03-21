# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:07:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:29:25
from enum import Enum, auto


class PostRating(Enum):
    """
    Ratings for Post objects
    """

    QUESTIONABLE = auto()
    SAFE = auto()
    EXPLICIT = auto()

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}

    @classmethod
    def choices(self):
        return [(choice, choice.name) for choice in self]

    @classmethod
    def coerce(self, item):
        return item if isinstance(item, self) else self(int(item))

    def __int__(self):
        return self.value

    def __str__(self):
        return str(self.value)
