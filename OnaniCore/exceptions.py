# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-15 17:19:32
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 20:31:23

from .utils import setup_logger

log = setup_logger(__name__)


class OnaniDatabaseException(Exception):
    """
    Common Exception for database errors
    """

    def __init__(self, msg=""):
        self.msg = msg
        log.error(msg)

    def __str__(self):
        return self.msg


class OnaniPermissionError(Exception):
    pass


class OnaniAuthenticationError(Exception):
    pass


class OnaniApiError(Exception):
    def __init__(self, msg="", code=400):
        self.msg = msg
        self.code = 400

    def __str__(self):
        return self.msg
