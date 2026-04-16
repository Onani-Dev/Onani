# -*- coding: utf-8 -*-

from typing import Optional

import requests
from flask import current_app
from Onani.services.posts import create_post
from Onani.services.files import get_file_data
from Onani.models import Post, User

from ._importedpost import ImportedPost
from . import db


def get_post(url: str) -> Optional[ImportedPost]:
    """Fetch post metadata from a URL via gallery-dl.

    Returns an ImportedPost on success, or None if the URL is not supported.
    """
    from .gallery_dl_importer import get_post as gdl_get_post, is_supported

    if not is_supported(url):
        return None

    return gdl_get_post(url)


def get_all_posts(url: str, cookies_path: str = None) -> list:
    """Fetch all posts from a URL (gallery support).

    Returns a list of ImportedPost objects — multiple for galleries, one for single posts.
    """
    from .gallery_dl_importer import get_all_posts as gdl_get_all_posts, is_supported

    if not is_supported(url):
        return []

    return gdl_get_all_posts(url, cookies_path=cookies_path)


def download_file(url: str) -> bytes:
    with requests.Session() as s:
        r = s.get(url)
        file_data = r.content
    return file_data


def save_imported_post(post: ImportedPost, importer_id: int) -> Post:

    file_data = download_file(post.file_url)

    (
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
    ) = get_file_data(file_data)

    user = User.query.filter_by(id=importer_id).first()
    can_create_tags = True

    return create_post(
        post.sources[0],
        post.description,
        user,
        post.rating.value,
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
        "Unknown",
        post.tags,
        images_dir=current_app.config["IMAGES_DIR"],
        can_create_tags=can_create_tags,
        tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
        post_min_tags=current_app.config["POST_MIN_TAGS"],
        imported_from=post.imported_url,
    )
