# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-09 01:56:43
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-08 08:39:59
import enum
from functools import cache


class NewsType(enum.Enum):
    ANNOUNCEMENT = 0
    MAINTENANCE = 1
    WARNING = 2
    COMMUNITY = 3
    UPDATE = 4
    POLL = 5
    DISCUSSION = 6

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.lower()

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
