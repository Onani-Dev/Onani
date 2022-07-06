# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-14 07:38:57
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-06 07:27:55


from typing import TYPE_CHECKING, Dict, Optional

import requests
from Onani.models import PostRating

from . import BaseImporter, ImportedPost


class DanbooruImporter(BaseImporter, URLs=["danbooru.donmai.us"]):
    """Importer for danbooru.donmai.us"""

    def _get_pid_from_url(self, url: str) -> Optional[str]:
        pid = url.split("/")[-1]
        if not pid.isdigit():
            return None
        return pid

    def _get_post_tags(self, json_data: Dict[str, str]):
        tags = []
        # There's gotta be a better way to do this right?
        for tag_type in ("general", "character", "copyright", "artist"):
            tags.extend(
                [
                    f"{tag_type}:{x}"
                    for x in json_data[f"tag_string_{tag_type}"].split(" ")
                ]
            )
        return tags

    def normalize_url(self, url: str) -> str:
        pid = self._get_pid_from_url(url)
        if not pid:
            raise ValueError("URL is missing the id")
        return f"https://{self.URL}/posts/{pid}"

    def get_post(self, url: str) -> Optional[ImportedPost]:
        pid = self._get_pid_from_url(url)

        if not pid:
            return None

        r = requests.get(f"https://{self.URL}/posts/{pid}.json").json()

        return ImportedPost(
            imported_url=self.normalize_url(url),
            tags=self._get_post_tags(r),
            sources=[r["source"]],
            file_url=r["file_url"],
            description="",
            rating=PostRating(r["rating"]),
        )
