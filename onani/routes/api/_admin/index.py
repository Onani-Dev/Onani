# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:37:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 06:40:11
from flask import jsonify
from onani.controllers import role_required
from onani.models import UserRoles

from . import admin_api, db


@admin_api.route("/", methods=["GET"])
@role_required(role=UserRoles.MODERATOR)
def api_index():
    return jsonify({"message": "wow admin"})
