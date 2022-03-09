# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:45:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:06:14
from marshmallow import fields
from Onani.models.post import Post

from . import ma


class PostSchema(ma.SQLAlchemyAutoSchema):
    file = ma.Nested("FileSchema")

    class Meta:
        model = Post
