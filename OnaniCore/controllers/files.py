# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-15 23:31:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-11 19:54:51

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

        avatar_md5, filesize, width, height, thumbnail = self._get_file_data(file_data)

        if width != height:
            raise ValueError("Width and height does not match")

        with open(f"{self.avatar_directory}{filename}", "wb") as f:
            f.write(file_data)

        return File(
            filename=filename,
            directory=self.avatar_directory.replace("./OnaniFrontend/static", ""),
            thumbnail=thumbnail,
            hash=avatar_md5,
            width=width,
            height=height,
            filesize=filesize,
        )

    def save_file(self, file_data: bytes, file_type: str) -> File:
        post_md5, filesize, width, height, thumbnail = self._get_file_data(
            file_data, make_thumbnail=True
        )

        filename = f"{post_md5}.{file_type}"

        if os.path.isfile(f"{self.post_directory}{filename}"):
            raise FileExistsError("File already exists.")

        with open(f"{self.post_directory}{filename}", "wb") as f:
            f.write(file_data)

        return File(
            filename=filename,
            directory=self.post_directory.replace("./OnaniFrontend/static", ""),
            thumbnail=thumbnail.replace("./OnaniFrontend/static", ""),
            hash=post_md5,
            width=width,
            height=height,
            filesize=filesize,
        )

    # INTERNAL FUNCTIONS
    def _get_file_data(self, file_data: bytes, make_thumbnail: bool = False) -> tuple:
        # The File-Like image object
        image_file = io.BytesIO(file_data)

        # Get MD5 hash
        hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()

        # Get filesize
        filesize = sys.getsizeof(file_data)

        # Delete file_data to save memory
        del file_data

        # Open and get width and height
        im = Image.open(image_file)
        width, height = im.size

        # Create Thumbnail if true
        thumbnail = None
        if make_thumbnail:
            im.thumbnail((170, 170), Image.ANTIALIAS)

        # Save the thumbnail
        if make_thumbnail:
            thumbnail = f"{self.thumb_directory}{hash_md5}.jpeg"
            if not os.path.isfile(thumbnail):
                im.convert("RGB").save(thumbnail, format="JPEG")

        # Return everything
        return hash_md5, filesize, width, height, thumbnail
