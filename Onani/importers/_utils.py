# -*- coding: utf-8 -*-

from typing import Optional

import requests
from flask import current_app
from Onani.services.posts import create_post
from Onani.services.files import get_file_data, get_video_data, is_video_url, detect_video_format
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


_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

# Byte prefixes that indicate an HTML/JSON error page rather than binary media
_TEXT_PREFIXES = (b"<!doctype", b"<html", b"{", b"[")


def download_file(url: str) -> bytes:
    with requests.Session() as s:
        r = s.get(url, headers=_DOWNLOAD_HEADERS, timeout=60)
        r.raise_for_status()
        data = r.content
    for prefix in _TEXT_PREFIXES:
        if data[: len(prefix)].lower() == prefix:
            raise ValueError(
                f"Server returned non-binary content for {url!r} "
                f"(starts with {data[:64]!r})"
            )
    return data


def save_imported_post(post: ImportedPost, importer_id: int) -> Post:
    from PIL import UnidentifiedImageError

    file_data = download_file(post.file_url)

    # Detect video format — first by URL extension, then by magic bytes
    video_fmt = None
    if is_video_url(post.file_url):
        video_fmt = post.file_url.split("?")[0].rsplit(".", 1)[-1].lower()
    else:
        video_fmt = detect_video_format(file_data)

    if video_fmt:
        (
            image_file,
            filesize,
            hash_sha256,
            hash_md5,
            width,
            height,
            filename,
            file_type,
        ) = get_video_data(file_data, input_format=video_fmt)
    else:
        # Try PIL; if it can't identify the file, try as an mp4 last resort
        try:
            import io as _io
            from PIL import Image as _Image
            _Image.open(_io.BytesIO(file_data)).verify()
        except UnidentifiedImageError:
            (
                image_file,
                filesize,
                hash_sha256,
                hash_md5,
                width,
                height,
                filename,
                file_type,
            ) = get_video_data(file_data, input_format="mp4")
        else:
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
