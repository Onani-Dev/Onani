# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 02:05:06
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-14 15:06:51

from typing import Optional, Tuple, Type

import requests
from Onani.controllers import create_post, get_file_data
from Onani.models import Post, User
from url_normalize import url_normalize
from werkzeug.urls import url_fix

from . import IMPORTERS, BaseImporter, ImportedPost, db


def find_importer(url: str) -> Optional[Type[BaseImporter]]:
    """
    Finds the appropriate importer from a URL
    This functions also handles normalising the URL
    """
    # First we fix and normalise the URL
    try:
        normalized_url = url_fix(url)
        # line bellow can raise exception with some weird URLs so we try/except
        normalized_url = url_normalize(normalized_url)
    except Exception as e:
        # URL was malformed, so we return None
        return None

    # Then we find the importer that corresponds to this url, if any
    for base_url in IMPORTERS.keys():
        if base_url in normalized_url:
            # This importer supports this site, we return it
            return IMPORTERS[base_url]

    # None of the importers support that site, we return None
    return None


def get_post(url: str) -> ImportedPost:
    """Gets a post using the available importers"""
    # First we try to find an importer
    i = find_importer(url)
    if not i:
        return None

    return i.get_post(url)


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

    post = create_post(
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
        post.imported_url,
    )

    return post
