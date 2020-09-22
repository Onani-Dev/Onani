# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-15 23:31:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-08-20 14:07:29

import hashlib
import os
from io import BytesIO


class DownloadController(object):
    pass


class FileController(object):
    """
    File Controller for Onani (Might be temporary idk will need to make one for amazon s3 or something)
    """

    __slots__ = ("location", "DLController")

    def __init__(self, location: str):
        if not os.path.isdir(location):
            raise ValueError("Path does not exist.")
        self.location = location

    def save_file(self, filebytes: bytes, filename: str = None):
        # TODO #15
        with open(f"{location}/{filename}", "wb") as f:
			f.write(filebytes)

    # INTERNAL FUNCTIONS
    def _get_md5(self, file: BytesIO):
        hash_md5 = hashlib.md5()
        with file as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
