# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-16 15:16:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:25:37
from enum import Flag, auto
from functools import reduce
from operator import or_ as _or_


class UserPermissions(Flag):
    CAN_POST = auto()
    CAN_FLAG = auto()
    PRIORITY_FLAG = auto()
    EDIT_POSTS = auto()

    CAN_COMMENT = auto()
    LOCK_COMMENTS = auto()
    DELETE_COMMENTS = auto()
    MERGE_POSTS = auto()

    BAN_USERS = auto()
    EDIT_COLLECTIONS = auto()

    @classmethod
    def all(cls):
        cls_name = cls.__name__
        if not cls:
            raise AttributeError(f"Empty {cls_name} does not have an ALL value")
        value = cls(reduce(_or_, cls))
        cls._member_map_["ALL"] = value
        return value

    @classmethod
    def none(cls):
        return cls(0)
