# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-13 00:37:46
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-06-15 13:17:38

import enum

class UserRoles(enum.Enum):
    """
    role for User models.
    """

    MEMBER = 0
    HELPER = 100
    MODERATOR = 200
    ADMIN = 300
    OWNER = 666

    def __int__(self):
        return self.value

    @classmethod
    def get_all(cls):
        return {e.name: e for e in cls}
