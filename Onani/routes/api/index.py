# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:01:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-16 00:02:08

from flask import jsonify, request

from . import main_api, make_api_response


@main_api.route("/", methods=["GET"])
def api_index():
    return make_api_response()
