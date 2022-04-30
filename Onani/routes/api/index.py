# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:01:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-30 15:05:13

from flask import jsonify, request
from flask_login import current_user
from Onani.tasks import test, database_test
from celery.result import AsyncResult
from . import main_api, make_api_response


@main_api.route("/", methods=["GET"])
def api_index():
    return make_api_response(
        {
            "permissions": current_user.permissions.value,
            "permissions_string": current_user.permissions.name,
        }
    )


@main_api.route("/test", methods=["GET"])
def test_endpoint():
    """Test endpoint

    Returns:
        Response: Fun
    """
    if r := request.args.get("id"):
        e: AsyncResult = database_test.AsyncResult(r)
        return make_api_response(
            {
                "result": e.result,
            }
        )
    e: AsyncResult = database_test.delay(current_user.id)
    return make_api_response(
        {
            "result": e.id,
        }
    )
