# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:26:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 23:50:22

import hashlib
import io
import os
import sys
from base64 import b64decode
from typing import List, Tuple
from urllib.request import urlopen

from flask_login import current_user
from Onani.models import File, Post, User
from PIL import Image

from . import db


def get_file_data(file_data: bytes, path: str = "/images/"):
    # The File-Like image object
    image_file = io.BytesIO(file_data)

    # Get filesize
    filesize = sys.getsizeof(file_data)

    # Delete file_data to save memory
    del file_data

    # Get MD5 hash
    hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()

    # Open and get width, height and file type
    im = Image.open(image_file)
    width, height = im.size
    file_type = im.format.lower()

    # The files URL to write to
    url = f"{path}{hash_md5}.{file_type}"

    return image_file, filesize, hash_md5, width, height, url


def create_files(post: Post, file_datas: List[bytes]) -> List[File]:
    for file_data in file_datas:
        image_file, filesize, hash_md5, width, height, url = get_file_data(file_data)

        # File is here to prevent writing to disk if this fails.
        file = File(
            url=url,
            hash=hash_md5,
            width=width,
            height=height,
            filesize=filesize,
        )

        # write to file
        with open(url, "wb") as f:
            image_file.seek(0)
            f.write(image_file.read())

        post.files.append(file)

    # Return the files
    return post.files


def create_avatar(user: User, base64_file: str) -> str:
    # get the base64 from the encoded url thingo idk the name dude
    avatar = b64decode(base64_file.split(",")[1])

    # The info
    image_file, filesize, hash_md5, width, height, url = get_file_data(
        avatar, path="/avatars/"
    )

    # Check the width and height
    if width != height:
        raise ValueError("Width and height does not match")

    # write to file
    with open(url, "wb") as f:
        image_file.seek(0)
        f.write(image_file.read())

    # delete current avatar
    if user.settings.avatar:
        os.remove(user.settings.avatar)

    # set new avatar
    user.settings.avatar = url

    db.session.commit()

    return url
