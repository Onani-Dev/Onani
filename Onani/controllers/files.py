# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:26:15
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 12:52:42

import hashlib
import io
import sys

from flask_login import current_user
from Onani.models import File, Post
from PIL import Image


def create_file(post: Post, file_data: bytes) -> File:
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
    url = f"/images/{hash_md5}.{file_type}"

    # write to file
    with open(url, "wb") as f:
        image_file.seek(0)
        f.write(image_file.read())

    post.uploader = current_user.id

    file = File(
        url=url,
        hash=hash_md5,
        width=width,
        height=height,
        filesize=filesize,
    )

    post.files.append(file)

    # Return the file
    return file
