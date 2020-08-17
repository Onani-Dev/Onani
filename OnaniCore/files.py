# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-15 23:31:53
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-17 20:27:48

import os


class FileController(object):
    """
    File Controller for Onani (Might be temporary idk will need to make one for amazon s3 or something)
    """

    __slots__ = "location"

    def __init__(self, location: str):
        self.location = location

