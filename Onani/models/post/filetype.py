# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-06-15 13:00:32
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-06-15 13:14:49

import enum

class FileType(enum.Enum):
    """
    Types for Tag Objects
    Can be: VIDEO or IMAGE
    """

    IMAGE = 0
    VIDEO = 1

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name.lower()

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}