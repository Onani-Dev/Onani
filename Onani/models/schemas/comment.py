# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:17:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:38:56
from marshmallow import fields
from Onani.models import PostComment

from . import ma


class PostCommentSchema(ma.SQLAlchemyAutoSchema):
    author = ma.auto_field()

    class Meta:
        model = PostComment
