# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:26:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-01 14:05:29

import hashlib
import io
import os
import sys
from base64 import b64decode
from typing import List, Tuple
from urllib.request import urlopen

from flask import current_app
from flask_login import current_user
from Onani.models import User
from PIL import Image

from . import db

"""All those functions are used by Post, but in a different file for posts.py not to be too long"""


def determine_meta_tags(
    width, height, filesize, file_type, tag_count=None
) -> list[str]:
    meta_tags = []

    # Determine width
    if width >= 5400 and height <= 512 or width <= 512 and height >= 5400:
        meta_tags.append("meta:long")

    elif width >= 10000 and height >= 10000:
        meta_tags.append("meta:extremely_high_resolution")

    elif width >= 3200 and height >= 2400:
        meta_tags.append("meta:very_high_resolution")

    elif width >= 1600 and height >= 1200:
        meta_tags.append("meta:high_resolution")

    elif width <= 500 and height <= 500:
        meta_tags.append("meta:low_resolution")

    # Determine filesize
    if filesize >= 15728640:
        meta_tags.append("meta:extremely_large_filesize")

    elif filesize >= 5242880:
        meta_tags.append("meta:large_filesize")

    # Determine file type
    if file_type == "gif":
        meta_tags.append("meta:animated")

    # Add tag_request tag for posts with less than 10 tags
    if tag_count & tag_count < current_app.config["POST_MIN_TAGS"]:
        meta_tags.append("meta:tag_request")

    return meta_tags


def get_file_data(file_data: bytes):
    # The File-Like image object
    image_file = io.BytesIO(file_data)

    # Get filesize
    filesize = sys.getsizeof(file_data)

    # Get MD5 hash
    hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()

    # Get SHA256 hash
    hash_sha256 = hashlib.sha256(image_file.getbuffer()).hexdigest()

    # Open and get width, height and file type
    im = Image.open(image_file)
    width, height = im.size
    file_type = im.format.lower()

    # The filename to write to
    filename = f"{hash_sha256}.{file_type}"

    return (
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
    )


def create_avatar(user: User, base64_file: str) -> str:
    # get the base64 from the encoded url thingo idk the name dude
    avatar = b64decode(base64_file.split(",")[1])

    # The info
    (
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
    ) = get_file_data(avatar)

    url = f"/avatars/{filename}"

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
