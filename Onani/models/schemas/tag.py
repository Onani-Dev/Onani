# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:03:33
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:11:44
from marshmallow import fields
from Onani.models import Tag

from . import ma


class TagSchema(ma.SQLAlchemyAutoSchema):
    alias_of = ma.auto_field()
    is_alias = fields.Bool()
    aliases = ma.Nested("TagSchema", many=True)
    posts = ma.Nested("PostSchema", many=True)

    class Meta:
        model = Tag
