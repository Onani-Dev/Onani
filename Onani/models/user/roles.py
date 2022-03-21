# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-13 00:37:46
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:28:45
from enum import Enum, auto


class UserRoles(Enum):
    """
    role for User models.
    """

    MEMBER = auto()
    ARTIST = auto()
    PREMIUM = auto()
    HELPER = auto()
    MODERATOR = auto()
    ADMIN = auto()
    OWNER = 666

    def __int__(self):
        return self.value

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}
