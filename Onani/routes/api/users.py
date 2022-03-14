# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:26:01
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-03-14 19:23:32

import json

from flask import abort, flash, jsonify, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from Onani.models import User, UserSchema

from . import admin_api, db, main_api, make_api_response

# @main_api.route("/user/<user_id>", methods=["GET"])
# @login_required
# def view_profile(user_id):
#     if not user_id.isdigit():
#         abort(404)

#     user_id = int(user_id)


@main_api.route("/users", methods=["GET"])
def get_users():
    page = request.args.get("page", "0")
    per_page = request.args.get("per_page", "10")

    page = int(page) if page.isdigit() else 0
    per_page = int(per_page) if per_page.isdigit() else 10

    users = User.query.paginate(per_page=per_page, page=page, error_out=False)

    user_schema = UserSchema(many=True)

    # hold up, this ain't no hot tub !!!!!!!!!
    return make_api_response(
        {
            "users": user_schema.dump(users.items),
            "next_page": users.next_num,
            "prev_page": users.prev_num,
            "total": users.total,
        }
    )
