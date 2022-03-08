# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:37:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 04:14:48
from flask import jsonify, request
from Onani.controllers import permissions_required
from Onani.models import UserPermissions

from . import admin_api, db


@admin_api.route("/", methods=["GET"])
@permissions_required(permissions=UserPermissions.MODERATOR)
def api_index():
    return jsonify({"message": "wow admin"})
