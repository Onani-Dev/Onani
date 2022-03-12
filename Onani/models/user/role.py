# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-13 00:37:46
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 00:55:06
import enum


class UserRoles(enum.Enum):
    """
    role for User models.
    """

    MEMBER = 1
    ARTIST = 2
    PREMIUM = 3
    HELPER = 4
    MODERATOR = 5
    ADMIN = 6
    OWNER = 666

    def __int__(self):
        return self.value

    @classmethod
    def get_all(self):
        return {e.name: e for e in self}
