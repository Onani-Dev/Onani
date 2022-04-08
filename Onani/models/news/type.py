# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-09 01:56:43
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-09 02:02:04
import enum


class NewsType(enum.Enum):
    ANNOUNCEMENT = enum.auto()
    MAINTENENCE = enum.auto()
    WARNING = enum.auto()
    COMMUNITY = enum.auto()
    UPDATE = enum.auto()

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}
