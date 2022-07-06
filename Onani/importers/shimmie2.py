# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-06 09:06:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-06 09:25:07

from typing import TYPE_CHECKING, Optional

import requests
import xmltodict
from Onani.models import PostRating

from . import BaseImporter, ImportedPost


class Shimmie2Importer(BaseImporter, URLs=["rule34.paheal.net"]):
    """Importer for rule34.paheal.net and most sites running shimmie2"""

    def _get_pid_from_url(self, url: str) -> Optional[str]:
        pid = url.split("/")[-1]
        if not pid.isdigit():
            return None
        return pid

    def normalize_url(self, url: str) -> str:
        pid = self._get_pid_from_url(url)
        if not pid:
            raise ValueError("URL is missing the id")
        return f"https://{self.URL}/post/view/{pid}"

    def get_post(self, url: str) -> Optional[ImportedPost]:
        pid = self._get_pid_from_url(url)
        if not pid:
            return None

        r = requests.get(
            f"https://{self.URL}/api/danbooru/find_posts",
            params={"id": pid},
        )

        r = xmltodict.parse(r.text)["posts"]["tag"]
        return ImportedPost(
            imported_url=self.normalize_url(url),
            tags=r["@tags"].split(" "),
            sources=[r["@source"]],
            file_url=r["@file_url"],
            description="",
            rating=PostRating.EXPLICIT,
        )
