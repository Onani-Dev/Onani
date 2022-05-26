# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-26 15:57:24
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-26 16:21:47
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import create_comment, permissions_required
from Onani.models import Post, PostSchema

from . import api, csrf, db, limiter


class Users(Resource):
    decorators = [login_required]

    def get(self):
        pass


# @main_api.route("/user", methods=["GET"])
# @login_required
# def get_user():
#     if id := request.args.get("id"):
#         if not id.isdigit():
#             abort(400)
#         user = User.query.filter_by(id=int(id)).first_or_404()

#     elif username := request.args.get("username"):
#         if len(username) > 32:
#             abort(400)
#         user = User.query.filter_by(username=username).first_or_404()
#     else:
#         abort(400)
#     return make_api_response({"data": UserSchema().dump(user)})


# @main_api.route("/users", methods=["GET"])
# @login_required
# def get_users():
#     page = request.args.get("page", "0")
#     per_page = request.args.get("per_page", "10")

#     page = int(page) if page.isdigit() else 0
#     per_page = int(per_page) if per_page.isdigit() else 10

#     users = User.query.paginate(per_page=per_page, page=page, error_out=False)

#     return make_api_response(
#         {
#             "data": UserSchema(many=True).dump(users.items),
#             "next_page": users.next_num,
#             "prev_page": users.prev_num,
#             "total": users.total,
#         }
#     )
