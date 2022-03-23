# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:26:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-24 03:26:15

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


def determine_meta_tags(width, height, filesize, file_type) -> list:
    meta_tags = []

    if width <= 500 and height <= 500:
        meta_tags.append("low_resolution")

    elif width >= 1600 and height >= 1200:
        meta_tags.append("high_resolution")

    elif width >= 3200 and height >= 2400:
        meta_tags.append("very_high_resolution")

    elif width >= 10000 and height >= 10000:
        meta_tags.append("extremely_high_resolution")

    elif width >= 5400 and height <= 512 or width <= 512 and height >= 5400:
        meta_tags.append("long")

    if filesize >= 5242880:
        meta_tags.append("large_filesize")

    elif filesize >= 15728640:
        meta_tags.append("extremely_large_filesize")

    if file_type == "gif":
        meta_tags.append("animated")

    return meta_tags


def get_file_data(file_data: bytes, path: str = "/images/"):
    # The File-Like image object
    image_file = io.BytesIO(file_data)

    # Get filesize
    filesize = sys.getsizeof(file_data)

    # Get MD5 hash
    hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()

    # Open and get width, height and file type
    im = Image.open(image_file)
    width, height = im.size
    file_type = im.format.lower()

    # The files URL to write to
    url = f"{path}{hash_md5}.{file_type}"

    return image_file, filesize, hash_md5, width, height, url, file_type


def create_files(post: Post, file_datas: List[bytes]) -> List[File]:
    meta_tags = []

    for file_data in file_datas:
        image_file, filesize, hash_md5, width, height, url, file_type = get_file_data(
            file_data
        )

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

        # Get meta tags based off of this shit idfk
        meta_tags.extend(determine_meta_tags(width, height, filesize, file_type))

    # Return the files
    return post.files, meta_tags


def create_avatar(user: User, base64_file: str) -> str:
    # get the base64 from the encoded url thingo idk the name dude
    avatar = b64decode(base64_file.split(",")[1])

    # The info
    image_file, filesize, hash_md5, width, height, url, file_type = get_file_data(
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
