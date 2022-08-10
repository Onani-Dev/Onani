# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-10 12:45:23
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 13:45:05

from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import create_avatar
from Onani.models import UserSchema, User

from . import api, db, limiter


class Profile(Resource):

    decorators = [login_required]

    def get(self):
        return UserSchema().dump(current_user)

    def put(self):
        parser = reqparse.RequestParser()

        # ACCOUNT SETTINGS
        parser.add_argument(
            "nickname", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "email", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "new_password", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "current_password", location="json", type=str, default=None, required=False
        )

        # PROFILE SETTINGS
        parser.add_argument(
            "biography", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "profile_picture", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "profile_colour", location="json", type=str, default=None, required=False
        )

        # Parse the args
        args = parser.parse_args()

        # ACCOUNT SETTINGS
        if args["nickname"]:
            current_user.nickname = args["nickname"]

        if args["email"]:
            current_user.email = args["email"]

        if args["new_password"] and current_user.check_password(
            args["current_password"]
        ):
            current_user.set_password(args["new_password"])

        # PROFILE SETTINGS
        if args["biography"]:
            current_user.settings.biography = args["biography"]

        if args["profile_colour"]:
            current_user.settings.profile_colour = args["profile_colour"]

        if args["profile_picture"]:
            create_avatar(current_user, args["profile_picture"])

        db.session.commit()

        return UserSchema().dump(current_user)

    def patch(self):
        return self.put()


api.add_resource(Profile, "/profile")
