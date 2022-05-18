# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 02:16:51
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-18 08:38:37


from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qs, urlparse

import requests
from Onani.models import PostRating

from . import BaseImporter, ImportedPost


class Ruler34Importer(BaseImporter, URLs=["rule34.xxx", "hypnohub.net"]):
    """Importer for rule34.xxx, and all other sites running Gelbooru Beta 0.2"""

    def _get_pid_from_url(self, url: str) -> Optional[str]:
        pid = parse_qs(urlparse(url).query).get("id")
        if not pid:
            # User might have given broken url where there is no id
            return None
        pid = pid[0]
        return pid

    def normalize_url(self, url: str) -> str:
        pid = self._get_pid_from_url(url)
        if not pid:
            raise ValueError("URL is missing the id")
        return f"https://{self.URL}/index.php?page=post&s=view&id={pid}"

    def get_post(self, url: str) -> Optional[ImportedPost]:
        pid = self._get_pid_from_url(url)
        if not pid:
            return None

        r = requests.get(
            f"https://api.{self.URL}/index.php",
            params={
                "page": "dapi",
                "s": "post",
                "q": "index",
                "json": "1",
                "id": pid,
            },
        )

        # It returns nothing if there's no post, not even empty json
        if not r.text:
            return None

        r = r.json()[0]
        return ImportedPost(
            tags=r["tags"].split(" "),
            sources=[self.normalize_url(url)],  # Rule34's API doesn't return source...
            file_urls=[r["file_url"]],
            description="",
            rating=PostRating.QUESTIONABLE,  # TODO CHANGE THESE TO THE ACTUAL VALUES
        )
