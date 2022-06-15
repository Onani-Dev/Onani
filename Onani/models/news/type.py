# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-09 01:56:43
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-06-15 13:15:23
import enum


class NewsType(enum.Enum):
    ANNOUNCEMENT = 0
    MAINTENENCE = 1
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
    def get_all(cls):
        return {e.name: e for e in cls}
