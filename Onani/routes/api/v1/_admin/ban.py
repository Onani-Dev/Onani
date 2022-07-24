# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-07-19 12:37:20
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-24 13:34:27
from email.policy import default
from flask_login import current_user, login_required
from flask_restful import Resource, inputs, reqparse
from Onani.controllers import create_ban, delete_ban, permissions_required
from Onani.models import Ban, UserPermissions
from Onani.models.schemas.ban import BanSchema
from Onani.models.schemas.user import UserSchema

from . import api


class BanUser(Resource):
    decorators = [login_required, permissions_required(UserPermissions.BAN_USERS)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", location="json", type=int, required=True)
        parser.add_argument(
            "expires", location="json", type=inputs.datetime_from_iso8601, default=None
        )
        parser.add_argument("reason", location="json", default="No reason specified.")

        parser.add_argument("delete_posts", location="json", type=bool, default=False)
        parser.add_argument("hide_posts", location="json", type=bool, default=False)

        data = parser.parse_args()

        ban = create_ban(
            user_id=data["user_id"],
            expires=data["expires"],
            reason=data["reason"],
            delete_posts=data["delete_posts"],
            hide_posts=data["hide_posts"],
        )

        return BanSchema().dump(ban)

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", location="json", type=int, required=True)

        data = parser.parse_args()

        user = delete_ban(user_id=data["user_id"])

        return UserSchema().dump(user)


api.add_resource(BanUser, "/admin/ban")
