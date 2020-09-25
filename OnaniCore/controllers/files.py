# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-15 23:31:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-25 13:37:39

import hashlib
import io
import os
import sys

from flask_login import current_user
from PIL import Image

from ..models import File


class DownloadController(object):
    pass


class FileController(object):
    """
    File Controller for Onani
    """

    __slots__ = ("avatar_directory", "post_directory", "thumb_directory")

    def __init__(
        self,
        avatar_directory: str = "./OnaniFrontend/static/data/avatars/",
        post_directory: str = "./OnaniFrontend/static/data/posts/",
        thumb_directory: str = "./OnaniFrontend/static/data/thumbs/",
    ):
        self.avatar_directory = avatar_directory
        self.post_directory = post_directory
        self.thumb_directory = thumb_directory

        if not os.path.isdir(avatar_directory):
            os.makedirs(avatar_directory)
        if not os.path.isdir(post_directory):
            os.makedirs(post_directory)
        if not os.path.isdir(thumb_directory):
            os.makedirs(thumb_directory)

    def save_avatar(self, file_data: bytes) -> File:
        filename = f"{hashlib.md5(str(current_user.id).encode()).hexdigest()}.png"

        avatar_md5, filesize, width, height = self._get_file_data(file_data)

        with open(f"{self.avatar_directory}{filename}", "wb") as f:
            f.write(file_data)

        return File(
            filename,
            self.avatar_directory.replace("./OnaniFrontend/static", ""),
            avatar_md5,
            width,
            height,
            filesize,
        )

    # INTERNAL FUNCTIONS
    def _get_file_data(self, file_data: bytes) -> tuple:
        # Hashlib md5 object thing for creating MD5 hash
        hash_md5 = hashlib.md5()

        # The File-Like image object
        image_file = io.BytesIO(file_data)

        # Get filesize
        filesize = sys.getsizeof(file_data)

        # Delete file_data to save memory
        del file_data

        # Open and get width and height
        im = Image.open(image_file)
        width, height = im.size

        # Get MD5
        with image_file as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        # Return everything
        return hash_md5.hexdigest(), filesize, width, height
