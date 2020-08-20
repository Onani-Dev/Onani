# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:57:03
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-21 00:31:53

import logging
import threading

import requests

from . import user_agent


log = logging.getLogger(__name__)


class Scraper:
    __slots__ = ("session", "base_url")

    def __init__(self, session=None, user_agent=None):
        self.session = session
        self.session.headers["User-Agent"] = self.user_agent


class DanBooruScraper(Scraper):
    def __init__(
        self,
        base_url: str = "https://danbooru.donmai.us",
        session: requests.Session = requests.Session(),
        user_agent: str = user_agent,
    ):
        self.base_url = base_url
        super().__init__(session=session, user_agent=user_agent)
