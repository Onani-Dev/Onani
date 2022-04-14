# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-15 01:43:24
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-15 01:54:59


class OnaniApiException(Exception):
    """Base exception for the Onani API"""

    def __init__(self, message: str, http_code: int = 500):
        super().__init__(message)

        self.http_code = http_code
