# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-15 20:29:55
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-15 22:02:48

from aenum import Enum, MultiValue


class UserPermissions(Enum):
    """
    Permissions for User objects.
    """

    _init_ = "value fullname"
    _settings_ = MultiValue

    MEMBER = 1, "Member"
    HELPER = 2, "Helper"
    MODERATOR = 3, "Moderator"
    ADMINISTRATOR = 4, "Administrator"
    OWNER = 666, "Owner"

    def __int__(self):
        return self.value

    def __str__(self):
        return self.fullname
