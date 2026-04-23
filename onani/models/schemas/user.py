# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:30:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-05 00:14:38
from marshmallow import fields
from onani.models.user import User, UserSettings

from . import ma


class SettingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserSettings
        exclude = ("id", "connections", "custom_css", "encrypted_cookies", "cookies_salt")


class UserSchema(ma.SQLAlchemyAutoSchema):

    ban = ma.Nested("BanSchema")
    settings = ma.Nested("SettingsSchema")
    avatar_thumbnail = fields.Str()

    class Meta:
        model = User
        exclude = (
            "password_hash",
            "otp_token",
            "comments",
            "posts",
            "email",
            "api_key",
            "tag_blacklist",
            "login_id",
        )
