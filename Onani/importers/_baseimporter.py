# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 01:35:26
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-01 03:41:43

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Type, Pattern
from . import ImportedPost


# IMPORTERS: List[Type[BaseImporter]] = []
# """
# A list of all classes that inherit from BaseImporter.
# Classes are added to it automatically as soon as they are loaded
# """

IMPORTERS: Dict[str, Type[BaseImporter]] = {}
"""
A dict of all supported sites as well as their matching importer
The key is the url to the site, and the value the importer
Classes are added to it automatically as soon as they are loaded
"""


class BaseImporter(ABC):
    """The base class that all other importers must inherit from"""

    # REGEXES: List[Pattern]
    # """
    # Regexes of the URLs to match for this importer, pre-compiled using re.compile().
    # The matching will be done with re.search().
    # The urls it will be matched again will be normalised in the "https://www.foo.com/foo" format.
    # Do be wary that http might be there too instead of https.
    # """
    # URLS: List[str]
    # """
    # URLs that this importer supports. Will be checked against with an "in" check against each URL.
    # The matching URL will be passed to the get_post method.
    # The urls it will be matched again will be normalised in the "https://www.foo.com/foo" format.
    # Do be wary that http might be there too instead of https.
    # """

    URL: str
    """The base URL of the site, that URLs will be matched again. Shouldn't be set manually."""

    def __init_subclass__(cls, URLs: List[str]) -> None:
        """Registers the subclass to IMPORTERS. One instance is made per url in URLs"""

        # We register instances of the importer to the dict
        # IMPORTERS.append(cls())
        for url in URLs:
            IMPORTERS[url] = cls(URL=url)

        return super().__init_subclass__()

    def __init__(self, URL: str) -> None:
        self.URL = URL
        super().__init__()

    @abstractmethod
    def get_post(self, url: str) -> Optional[ImportedPost]:
        """Gets a post from the site. May return None."""
        pass

    def normalize_url(self, url: str) -> str:
        """
        Standardises a URL from that site.
        You don't HAVE to add it, but it'd be nice if you did
        """
        return url
