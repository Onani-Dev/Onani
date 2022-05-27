# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:45:40
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 23:30:21
from marshmallow import fields
from marshmallow_sqlalchemy import auto_field
from Onani.models import Post

from . import ma


class PostSchema(ma.SQLAlchemyAutoSchema):
    files = ma.Nested("FileSchema", many=True)

    class Meta:
        model = Post
        include_fk = True

    tag_string = fields.Str(dump_only=True, data_key="tags")
    title = fields.Str(dump_only=True)
