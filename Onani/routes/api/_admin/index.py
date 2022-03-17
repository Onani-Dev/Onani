# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:37:30
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-03-17 21:18:00
from flask import jsonify, request
from Onani.controllers import role_required
from Onani.models import UserRoles

from . import admin_api, db


@admin_api.route("/", methods=["GET"])
@role_required(role=UserRoles.MODERATOR)
def api_index():
    return jsonify({"message": "wow admin"})
