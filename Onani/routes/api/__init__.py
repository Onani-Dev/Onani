# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:42:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-16 01:11:14


from json import dumps
from typing import Tuple

from flask import Response

from .. import admin_api, csrf, db, main_api


def make_api_response(
    data: dict = dict(), error: str = None, code: int = 200
) -> Tuple[Response, int]:
    ok = code not in range(400, 600)
    data["ok"] = ok
    data["error"] = error
    return (
        Response(dumps(data), mimetype="application/json"),
        code,
    )


from . import _admin, index, news, posts, profile, tags, users
