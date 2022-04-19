# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:37:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-19 18:10:40
from flask import jsonify, request, abort
from Onani.controllers import role_required
from Onani.models import UserRoles, Ban, User

from . import admin_api, db, csrf
from .. import make_api_response


@admin_api.route("/ban", methods=["POST", "DELETE"])
@role_required(role=UserRoles.ADMIN)
@csrf.exempt
def ban_user():

    if request.method == "POST":
        # check if data is json data
        data = request.json
        if not data:
            abort(400)
        bans = []
        ban = Ban()
        ban.expires = data["expires"]
        ban.reason = data["reason"]

        ban.save_to_db()
        return make_api_response()


# @admin_api.route("/pardon", methods=["POST"])
# @role_required(role=UserRoles.MODERATOR)
# @csrf.exempt
# def unban_user():
#     data = request.json
#     ban = Ban(
#             user=data["user_id"],
#             expires=data["expires"],
#             reason=data["reason"],
#         )
#     Ban.query.filter_by(data["user_id"]).all()
#     # You know what to do, I won't, I can't.
#     ban.save_to_db()
#     return make_api_response()
