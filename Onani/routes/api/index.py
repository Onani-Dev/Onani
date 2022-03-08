# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:01:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 03:02:21

from flask import jsonify, request

from . import main_api


@main_api.route("/", methods=["GET"])
def api_index():
    return jsonify({"message": request.remote_addr})
