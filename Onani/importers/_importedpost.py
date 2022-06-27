# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 02:33:26
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-27 02:24:21

from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from Onani.models import PostRating


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

    file_urls: List[str]
    """All the files from that post that will need to be downloaded"""

    description: str
    """The description for the post"""

    rating: PostRating
    """The rating for the post."""
