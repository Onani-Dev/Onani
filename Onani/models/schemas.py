# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-16 20:35:46
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 00:34:41

from marshmallow import fields
from Onani.models.ban import Ban
from Onani.models.collection import Collection
from Onani.models.comment import PostComment
from Onani.models.file import File
from Onani.models.news import NewsPost
from Onani.models.post import Post
from Onani.models.tag import Tag
from Onani.models.user import User, UserSettings

from .. import ma


class UserSchema(ma.SQLAlchemyAutoSchema):

    tag_blacklist = ma.Nested("TagSchema", many=True)
    ban = ma.Nested("BanSchema")
    settings = ma.Nested("SettingsSchema")

    class Meta:
        model = User


class TagSchema(ma.SQLAlchemyAutoSchema):
    alias_of = ma.auto_field()
    is_alias = fields.Bool()
    aliases = ma.Nested("TagSchema", many=True)
    posts = ma.Nested("PostSchema", many=True)

    class Meta:
        model = Tag


class FileSchema(ma.SQLAlchemyAutoSchema):
    post = ma.auto_field()

    class Meta:
        model = File


class PostSchema(ma.SQLAlchemyAutoSchema):
    file = ma.Nested("FileSchema")

    class Meta:
        model = Post


class BanSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ban


class CollectionSchema(ma.SQLAlchemyAutoSchema):
    posts = ma.Nested("PostSchema", many=True)
    creator = ma.auto_field()

    class Meta:
        model = Collection


class SettingsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserSettings


class NewsPostSchema(ma.SQLAlchemyAutoSchema):
    author = ma.auto_field()

    class Meta:
        model = NewsPost


class PostCommentSchema(ma.SQLAlchemyAutoSchema):
    author = ma.auto_field()

    class Meta:
        model = PostComment


# user_schema = UserSchema(exclude=["password_hash", "api_key"])
# user_schemas = UserSchema(exclude=["password_hash", "api_key"], many=True)

# tag_schema = TagSchema()
# tag_schemas = TagSchema(many=True)

# post_schema = PostSchema()
# post_schemas = PostSchema(many=True)

# ban_schema = BanSchema()
# ban_schemas = BanSchema(many=True)

# collection_schema = CollectionSchema()
# collection_schemas = CollectionSchema(many=True)
