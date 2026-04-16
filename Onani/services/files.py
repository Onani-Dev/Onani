# -*- coding: utf-8 -*-
import contextlib
import hashlib
import io
import os
import sys
from base64 import b64decode
from typing import Tuple

from Onani.models import User
from PIL import Image

from Onani import db


def determine_meta_tags(
    width: int,
    height: int,
    filesize: int,
    file_type: str,
    min_tags: int,
    tag_count: int | None = None,
) -> list[str]:
    """Return a list of meta tag names to apply based on image dimensions/size.

    Args:
        min_tags: Minimum required tag count (from config).
        tag_count: Current tag count; if below min_tags adds meta:tag_request.
    """
    meta_tags = []

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

    if filesize >= 15728640:
        meta_tags.append("meta:extremely_large_filesize")
    elif filesize >= 5242880:
        meta_tags.append("meta:large_filesize")

    if file_type == "gif":
        meta_tags.append("meta:animated")

    if tag_count is not None and tag_count < min_tags:
        meta_tags.append("meta:tag_request")

    return meta_tags


def get_file_data(
    file_data: bytes,
) -> Tuple[io.BytesIO, int, str, str, int, int, str, str]:
    """Parse raw file bytes, compute hashes and image dimensions.

    Returns:
        (image_file, filesize, sha256, md5, width, height, filename, file_type)
    """
    image_file = io.BytesIO(file_data)
    filesize = sys.getsizeof(file_data)
    hash_md5 = hashlib.md5(image_file.getbuffer()).hexdigest()
    hash_sha256 = hashlib.sha256(image_file.getbuffer()).hexdigest()

    im = Image.open(image_file)
    width, height = im.size
    file_type = im.format.lower()

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


def create_avatar(user: User, base64_file: str, avatars_dir: str) -> str:
    """Decode a base64 image, save it as the user's avatar, and return the URL.

    Args:
        user: The user whose avatar to update.
        base64_file: A data-URL string (e.g. ``data:image/png;base64,...``).
        avatars_dir: Filesystem path where avatars are stored (from config).

    Raises:
        ValueError: If the image is not square.
    """
    avatar = b64decode(base64_file.split(",")[1])

    (
        image_file,
        _filesize,
        hash_sha256,
        _hash_md5,
        width,
        height,
        filename,
        _file_type,
    ) = get_file_data(avatar)

    if width != height:
        raise ValueError("Width and height do not match — avatar must be square.")

    url = f"/avatars/{filename}"
    filepath = os.path.join(avatars_dir, filename)

    with open(filepath, "wb") as f:
        image_file.seek(0)
        f.write(image_file.read())

    if user.settings.avatar:
        old_path = os.path.join(avatars_dir, os.path.basename(user.settings.avatar))
        with contextlib.suppress(FileNotFoundError):
            os.remove(old_path)

    user.settings.avatar = url
    db.session.commit()

    return url
