# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:42:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-02 01:39:37


from json import dumps
from typing import Tuple

from flask import Response

from .. import admin_api, csrf, db, main_api


def make_api_response(
    data: dict = None, error: str = None, code: int = 200
) -> Tuple[Response, int]:
    """Create a standardised response for the api.

    Args:
        data (dict, optional): The JSON data to return. Defaults to None.
        error (str, optional): The error, if applicable. Defaults to None.
        code (int, optional): The HTTP code. Defaults to 200.

    Returns:
        Tuple[Response, int]: The Response and HTTP code.
    """
    if data is None:
        data = {}
    ok = code not in range(400, 600)
    data["ok"] = ok
    data["error"] = error
    return (
        Response(dumps(data), mimetype="application/json"),
        code,
    )


from . import _admin, comments, index, news, posts, profile, tags, users, importer
