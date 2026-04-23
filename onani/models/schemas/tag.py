# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:03:33
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-24 19:25:12
# sourcery skip: avoid-builtin-shadow
from marshmallow import fields
from onani.models import Tag

from . import ma


class TagSchema(ma.SQLAlchemyAutoSchema):
    alias_of = ma.auto_field()
    aliases = ma.Nested("TagSchema", many=True, exclude=("posts",))
    is_alias = fields.Bool()
    posts = ma.Nested("PostSchema", many=True)
    type = fields.String()
    humanized = fields.String()

    class Meta:
        model = Tag
