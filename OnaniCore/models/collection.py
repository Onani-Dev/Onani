# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-22 01:03:56
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-22 18:44:22

import logging
from datetime import datetime
from typing import List
from aenum import Enum, MultiValue

log = logging.getLogger(__name__)


class CollectionStatus(Enum):
    """
    Status for collections
    """

    _init_ = "value string"
    _settings_ = MultiValue

    BANNED = 0, "Banned"
    PENDING = 1, "Pending"
    ACCEPTED = 2, "Accepted"

    def __int__(self):
        return self.value


# Iwant die
class Collection(object):

    __slots__ = (
        "_db",
        "id",
        "title",
        "description",
        "posts",
        "status" "created_at",
        "creator",
        "rating",
    )

