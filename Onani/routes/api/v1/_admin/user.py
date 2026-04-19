# -*- coding: utf-8 -*-
"""Admin user-edit endpoint — GET/PUT /admin/user."""
from flask import abort
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from marshmallow import fields as ma_fields

from Onani.controllers import permissions_required
from Onani.models import User, UserPermissions, UserRoles
from Onani.models.schemas import ma
from Onani.models.schemas.user import SettingsSchema

from . import api, db


class AdminUserSchema(ma.SQLAlchemyAutoSchema):
    """Full user schema for admins — includes email, raw permissions/role ints."""

    ban = ma.Nested("BanSchema")
    settings = ma.Nested(SettingsSchema)
    avatar_thumbnail = ma_fields.Str()
    permissions_int = ma_fields.Method("get_permissions_int")
    role_int = ma_fields.Method("get_role_int")

    def get_permissions_int(self, obj):
        return int(obj.permissions)

    def get_role_int(self, obj):
        return obj.role.value

    class Meta:
        model = User
        exclude = ("password_hash", "otp_token", "comments", "posts", "api_key", "tag_blacklist", "login_id")


_ROLE_MAP = {r.name: r for r in UserRoles}


class AdminUser(Resource):
    decorators = [login_required, permissions_required(UserPermissions.EDIT_USERS)]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", location="args", type=int, required=True)
        args = parser.parse_args()

        user = User.query.filter_by(id=args["user_id"]).first_or_404()
        return AdminUserSchema().dump(user)

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", location="json", type=int, required=True)
        parser.add_argument("username", location="json", default=None)
        parser.add_argument("nickname", location="json", default=None, store_missing=False)
        parser.add_argument("email", location="json", default=None, store_missing=False)
        parser.add_argument("password", location="json", default=None)
        parser.add_argument("role", location="json", default=None)
        parser.add_argument("permissions", location="json", type=int, default=None)
        args = parser.parse_args()

        user = User.query.filter_by(id=args["user_id"]).first_or_404()

        # Prevent editing users with an equal or higher role
        if user.role.value >= current_user.role.value:
            abort(403, description="Cannot edit a user with an equal or higher role.")

        try:
            if args["username"] is not None and args["username"] != user.username:
                user.username = args["username"]

            if "nickname" in args:
                nick = args["nickname"]
                if nick != user.nickname:
                    user.nickname = nick if nick else None

            if "email" in args:
                email = args["email"]
                if email != user.email:
                    user.email = email if email else None

            if args["password"]:
                if len(args["password"]) < 8:
                    abort(400, description="Password must be at least 8 characters.")
                user.set_password(args["password"])

            if args["role"] is not None:
                new_role = _ROLE_MAP.get(args["role"])
                if new_role is None:
                    abort(400, description=f"Unknown role '{args['role']}'.")
                # Can only grant up to (but not including) the actor's own role
                if new_role.value >= current_user.role.value:
                    abort(403, description="Cannot assign a role equal to or higher than your own.")
                user.role = new_role

            if args["permissions"] is not None:
                try:
                    new_perms = UserPermissions(args["permissions"])
                except ValueError:
                    abort(400, description="Invalid permissions value.")
                user.permissions = new_perms

            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            abort(400, description=str(e))

        return AdminUserSchema().dump(user)


api.add_resource(AdminUser, "/admin/user")
