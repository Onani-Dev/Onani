# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:07:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 14:26:35
import enum


class PostStatus(enum.Enum):
    """
    Status for Post objects
    """

    REMOVED = 0
    PENDING = 1
    APPROVED = 2
    OBLITERATED = 3

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
