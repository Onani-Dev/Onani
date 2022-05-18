# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-01 23:57:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-18 08:42:34
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Tuple, Union

import requests
from bs4 import BeautifulSoup

from . import BaseImporter, ImportedPost

from Onani.models import PostRating


class DeviantArtImporter(BaseImporter, URLs=["deviantart.com", "www.deviantart.com"]):
    """Importer for the site DEVIANTFART"""

    BEARER_URL = "https://www.deviantart.com/oauth2/token?grant_type=client_credentials&with_session=true&mature_content=1"
    BEARER_PAYLOAD = "client_id=1700&client_secret=390a526b293e50ad52c729aff198d697a34bd13cd4d10f6484d9dbfd8a25ab66"
    BEARER_HEADERS = {
        "Host": "www.deviantart.com",
        "Da-Session-Id": "5fed3074052019bee084e20e75d8f8d0",
        "Da-Minor-Version": "20210526",  # 😭😭😭😭 - Dirt is a PDF File
        "User-Agent": "DeviantFart-Android/6.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.session = requests.session()
        self._access_token = None

    @property
    def access_token(self) -> str:
        """The access token.

        Returns:
            str: Access token
        """
        if not self._access_token:
            self._access_token = self._generate_bearer_token()
        return self._access_token

    def _determine_rating(self, rating: bool) -> PostRating:
        return PostRating.EXPLICIT if rating else PostRating.SAFE

    def _get_uuid(self, post_url: str):
        """Get the UUID of a deviantart post

        Args:
            post_url (str): The post URL to get the UUID from

        Returns:
            str: Post UUID
        """
        response = self.session.get(post_url)
        soup = BeautifulSoup(response.text, "lxml")
        element = soup.find("meta", property="da:appurl")
        return element["content"].split("/")[-1]

    def _generate_bearer_token(self) -> str:
        """Generate a bearer token to access DA

        Returns:
            str: the access token
        """
        response = self.session.post(
            self.BEARER_URL, headers=self.BEARER_HEADERS, data=self.BEARER_PAYLOAD
        )
        data = response.json()
        return data["access_token"]

    def _get_post_image(self, deviation: Dict) -> Union[str, None]:
        """Get the highest quality image from a post (if available)

        Args:
            deviation (NamedTuple): The post data

        Returns:
            Union[str, None]: Post Image url (None if not available)
        """
        match deviation["is_downloadable"]:
            case True:
                params = {
                    "access_token": self.access_token,
                    "with_session": True,
                    "mature_content": 1,
                }
                response = self.session.get(
                    f"https://www.deviantart.com/api/v1/oauth2/deviation/download/{deviation['deviationid']}",
                    params=params,
                )
                data = response.json()
                return data["src"]
            case False:
                return deviation["content"]["src"]
            case _:
                return None

    def _get_meta(self, post_uuid: str) -> Tuple[str, str, List[str]]:
        meta = {
            "access_token": self.access_token,
            "deviationids": post_uuid,
            "ext_submission": True,
            "ext_camera": True,
            "ext_stats": True,
            "ext_gallery": False,
            "ext_collection": False,
            "with_session": True,
            "mature_content": 1,
        }
        response = self.session.get(
            "https://www.deviantart.com/api/v1/oauth2/deviation/metadata", params=meta
        )
        data = response.json()["metadata"][0]

        return (
            data["description"],
            data["author"]["username"],
            [t["tag_name"] for t in data["tags"]],
        )

    def get_post(self, url: str) -> NamedTuple:
        """Get the post from a DA URL

        Args:
            post_url (str): The DA URL to get the post from

        Returns:
            NamedTuple: Lazy mf.
        """
        post_uuid = self._get_uuid(url)
        params_deviation = {
            "access_token": self.access_token,
            "expand": "user.watch%2Cdeviation.fulltext",
            "with_session": True,
            "mature_content": 1,
        }
        response = self.session.get(
            f"https://www.deviantart.com/api/v1/oauth2/deviation/{post_uuid}",
            params=params_deviation,
        )

        data = response.json()
        image = self._get_post_image(data)
        description, user, tags = self._get_meta(post_uuid)
        return ImportedPost(
            tags=tags,
            sources=[url],
            file_urls=[image],
            description=description,
            rating=self._determine_rating(data["is_mature"]),
        )
