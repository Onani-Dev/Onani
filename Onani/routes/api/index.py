# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:01:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-26 01:33:45

from flask import jsonify, request
from flask_login import current_user
from Onani.tasks import test
from . import main_api, make_api_response


@main_api.route("/", methods=["GET"])
def api_index():
    t = test.send("Monkey")
    return make_api_response(
        {
            "result": t.get_result(),
        }
    )


# return make_api_response(
#     {
#         "permissions": current_user.permissions.value,
#         "permissions_string": current_user.permissions.name,
#     }
# )
