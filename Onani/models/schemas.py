# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 20:35:46
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-17 03:09:37

from marshmallow import fields
from Onani.models.ban import Ban
from Onani.models.post import Post
from Onani.models.tag import Tag
from Onani.models.user import User

from .. import ma


class UserSchema(ma.SQLAlchemyAutoSchema):

    tag_blacklist = ma.Nested("TagSchema", many=True)
    ban = ma.Nested("BanSchema")

    class Meta:
        model = User


class TagSchema(ma.SQLAlchemyAutoSchema):
    alias_of = ma.auto_field()
    is_alias = fields.Bool()
    aliases = ma.Nested("TagSchema", many=True)
    posts = ma.Nested("PostSchema", many=True)

    class Meta:
        model = Tag


class PostSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Post


class BanSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ban


user_schema = UserSchema(exclude=["password_hash", "api_key"])
user_schemas = UserSchema(exclude=["password_hash", "api_key"], many=True)

tag_schema = TagSchema()
tag_schemas = TagSchema(many=True)

post_schema = PostSchema()
post_schemas = PostSchema(many=True)

ban_schema = BanSchema()
ban_schemas = BanSchema(many=True)
