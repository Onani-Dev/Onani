# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:30:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-03 18:13:02
from Onani.models.user import User, UserSettings

from . import ma


class SettingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserSettings
        exclude = ("id", "connections", "custom_css")


class UserSchema(ma.SQLAlchemyAutoSchema):

    ban = ma.Nested("BanSchema")
    settings = ma.Nested("SettingsSchema")

    class Meta:
        model = User
        exclude = (
            "password_hash",
            "comments",
            "posts",
            "email",
            "api_key",
            "tag_blacklist",
            "login_id",
        )
