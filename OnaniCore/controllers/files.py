# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-15 23:31:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-25 00:48:44

import hashlib
import io
import os

from flask_login import current_user
from PIL import Image

from ..models import File


class DownloadController(object):
    pass


class FileController(object):
    """
    File Controller for Onani
    """

    __slots__ = ("avatar_directory", "post_directory")

    def __init__(
        self,
        avatar_directory: str = "./OnaniFrontend/static/data/avatars/",
        post_directory: str = "./OnaniFrontend/static/data/posts/",
    ):
        self.avatar_directory = avatar_directory
        self.post_directory = post_directory

        if not os.path.isdir(avatar_directory):
            os.makedirs(avatar_directory)
        if not os.path.isdir(post_directory):
            os.makedirs(post_directory)

    def save_avatar(self, filebytes: bytes) -> File:
        filename = f"{hashlib.md5(str(current_user.id).encode()).hexdigest()}.png"
        avatar_md5 = hashlib.md5(filebytes).hexdigest()

        im = Image.open(io.BytesIO(filebytes))
        width, height = im.size

        with open(f"{self.avatar_directory}{filename}", "wb") as f:
            f.write(filebytes)

        return File(
            filename,
            self.avatar_directory.replace("./OnaniFrontend/static", ""),
            avatar_md5,
            width,
            height,
        )

    # # INTERNAL FUNCTIONS
    # def _get_md5(self, file_bytes: bytes) -> str:
    #     return hashlib.md5(file_bytes).hexdigest()
