# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:17:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-03 18:51:00
from marshmallow import fields
from Onani.models import PostComment

from . import ma


class PostCommentSchema(ma.SQLAlchemyAutoSchema):
    author = ma.Nested("UserSchema", exclude=("post_count",))

    class Meta:
        model = PostComment
        exclude = ("author_id",)  # "post_id"
