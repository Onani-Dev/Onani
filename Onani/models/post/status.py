# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:07:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:08:21
import enum


class PostStatus(enum.Enum):
    """
    Status for Post objects
    """

    DELETED = 0
    ACTIVE = 1

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}

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
