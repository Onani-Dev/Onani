# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:03:33
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-20 22:44:41
# sourcery skip: avoid-builtin-shadow
from marshmallow import fields
from Onani.models import Tag

from . import ma


class TagSchema(ma.SQLAlchemyAutoSchema):
    alias_of = ma.auto_field()
    aliases = ma.Nested("TagSchema", many=True)
    is_alias = fields.Bool()
    posts = ma.Nested("PostSchema", many=True)
    type = fields.String()
    humanized = fields.String()

    class Meta:
        model = Tag
