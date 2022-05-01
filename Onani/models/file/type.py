# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-01 21:55:41
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-01 22:15:46
import enum


class FileType(enum.Enum):
    """
    Types for Tag Objects
    Can be: VIDEO or IMAGE
    """

    IMAGE = enum.auto()
    VIDEO = enum.auto()

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}
