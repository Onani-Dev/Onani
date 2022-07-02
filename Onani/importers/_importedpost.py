# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 02:33:26
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-02 08:11:41

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from flask_login import current_user
from Onani.controllers import create_post, get_file_data
from Onani.models import Post, PostRating

from ._utils import download_file

from . import db


@dataclass
class ImportedPost:
    """
    Represents a post that was scraped by an importer.
    This class is only used to store that data in a standardised way, and does
    not represent a post on Onani in any way.
    """

    imported_url: str
    """The URL that the post has been imported from."""

    tags: List[str]
    """The tags of the post"""

    sources: List[str]
    """
    The sources of the post. it SHOULD include the URL used to scrape it,
    preferably in a standardised format (per importer).
    """

    file_url: str
    """The file from that post that will need to be downloaded"""

    description: str
    """The description for the post"""

    rating: PostRating
    """The rating for the post."""

    def save(self) -> Post:
        """Save the imported post to the database

        Returns:
            Post: The Actual post
        """
        file_data = download_file(self.file_url)

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

        post = create_post(
            self.sources[0],
            self.description,
            current_user,
            self.rating.value,
            image_file,
            filesize,
            hash_sha256,
            hash_md5,
            width,
            height,
            filename,
            file_type,
            "Unknown",
            self.tags,
        )

        db.session.add(post)

        db.session.commit()

        return post
