# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:45:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 23:31:38
from marshmallow import fields
from Onani.models import Post

from . import ma


class PostSchema(ma.SQLAlchemyAutoSchema):
    files = ma.Nested("FileSchema", many=True)

    class Meta:
        model = Post
