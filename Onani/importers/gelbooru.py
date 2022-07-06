# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-06 08:40:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-06 08:55:16
from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qs, urlparse

import requests
from Onani.models import PostRating

from . import BaseImporter, ImportedPost


class GelbooruImporter(BaseImporter, URLs=["gelbooru.com"]):
    """Importer for gelbooru.com"""

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
            f"https://{self.URL}/index.php",
            params={
                "page": "dapi",
                "s": "post",
                "q": "index",
                "json": "1",
                "id": pid,
            },
        )

        r = r.json()["post"][0]

        return ImportedPost(
            imported_url=self.normalize_url(url),
            tags=r["tags"].split(" "),
            sources=[r["source"]],
            file_url=r["file_url"],
            description="",
            rating=PostRating(r["rating"][:1]),
        )
