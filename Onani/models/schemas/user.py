# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:30:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 01:16:06
from Onani.models.user import User, UserSettings

from . import ma


class SettingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserSettings
        exclude = ("id",)


class UserSchema(ma.SQLAlchemyAutoSchema):

    ban = ma.Nested("BanSchema")
    settings = ma.Nested("SettingsSchema")
    tag_blacklist = ma.Nested("TagSchema", many=True)

    class Meta:
        model = User
        exclude = ("password_hash", "comments", "posts")
