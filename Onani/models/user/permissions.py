# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-16 15:16:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-20 16:02:57
from enum import IntFlag, auto

# from functools import reduce
# from operator import or_ as _or_


class UserPermissions(IntFlag):
    """User Permissions Flags"""

    # POSTS
    CREATE_POSTS = auto()
    DELETE_POSTS = auto()
    EDIT_POSTS = auto()
    IMPORT_POSTS = auto()
    MERGE_POSTS = auto()

    # TAGS
    CREATE_TAGS = auto()
    DELETE_TAGS = auto()
    EDIT_TAGS = auto()
    IMPORT_TAGS = auto()
    MERGE_TAGS = auto()

    # COLLECTIONS
    CREATE_COLLECTIONS = auto()
    DELETE_COLLECTIONS = auto()
    EDIT_COLLECTIONS = auto()
    MERGE_COLLECTIONS = auto()

    # FLAGGING
    CAN_FLAG = auto()
    PRIORITY_FLAG = auto()

    # COMMENTS
    CREATE_COMMENTS = auto()
    DELETE_COMMENTS = auto()
    LOCK_COMMENTS = auto()

    # NEWS
    CREATE_NEWS = auto()
    DELETE_NEWS = auto()
    EDIT_NEWS = auto()

    # USERS
    BAN_USERS = auto()
    CREATE_USERS = auto()
    DELETE_USERS = auto()
    EDIT_USERS = auto()

    # SITE
    BYPASS_RATELIMIT = auto()
    VIEW_LOGS = auto()

    # PRESETS
    READONLY = 0

    DEFAULT = CREATE_POSTS | CREATE_COMMENTS | CREATE_COLLECTIONS | CAN_FLAG

    TRUSTED = DEFAULT | CREATE_TAGS | IMPORT_POSTS | PRIORITY_FLAG

    MODERATION = (
        TRUSTED
        | EDIT_POSTS
        | MERGE_POSTS
        | EDIT_TAGS
        | MERGE_TAGS
        | EDIT_COLLECTIONS
        | MERGE_COLLECTIONS
        | DELETE_COMMENTS
        | LOCK_COMMENTS
    )

    ADMINISTRATION = (
        MODERATION
        | DELETE_POSTS
        | DELETE_TAGS
        | DELETE_COLLECTIONS
        | CREATE_NEWS
        | DELETE_NEWS
        | EDIT_NEWS
        | BAN_USERS
        | CREATE_USERS
        | DELETE_USERS
        | EDIT_USERS
        | BYPASS_RATELIMIT
        | VIEW_LOGS
    )

    # @classmethod
    # def all(cls):
    #     cls_name = cls.__name__
    #     if not cls:
    #         raise AttributeError(f"Empty {cls_name} does not have an ALL value")
    #     value = cls(reduce(_or_, cls))
    #     cls._member_map_["ALL"] = value
    #     return value

    # @classmethod
    # def none(cls):
    #     return cls(0)
