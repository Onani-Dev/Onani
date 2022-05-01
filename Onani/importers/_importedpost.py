# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 02:33:26
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-01 02:37:15

from dataclasses import dataclass
from typing import List


@dataclass
class ImportedPost:
    """
    Represents a post that was scraped by an importer.
    This class is only used to store that data in a standardised way, and does
    not represent a post on Onani in any way.
    """

    tags: List[str]
    """The tags of the post"""
    sources: List[str]
    """
    The sources of the post. it SHOULD include the URL used to scrape it,
    preferably in a standardised format (per importer).
    """
    file_urls: List[str]
    """All the files from that post that will need to be downloaded"""
