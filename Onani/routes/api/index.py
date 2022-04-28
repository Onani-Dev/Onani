# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:01:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:45:07

from flask import jsonify, request
from flask_login import current_user
from Onani.tasks import test
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
    e: AsyncResult = test.delay("Monki")
    return make_api_response(
        {
            "result": e.id,
        }
    )
