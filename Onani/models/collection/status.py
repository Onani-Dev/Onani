# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-21 23:10:46
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:11:34
import enum


class CollectionStatus(enum.Enum):
    """
    Status for collections
    """

    BANNED = 0
    PENDING = 1
    ACCEPTED = 2

    def __int__(self):
        return self.value

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}
