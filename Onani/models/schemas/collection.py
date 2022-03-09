# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:14:09
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:18:05
from marshmallow import fields
from Onani.models import Collection

from . import ma


class CollectionSchema(ma.SQLAlchemyAutoSchema):
    posts = ma.Nested("PostSchema", many=True)
    creator = ma.auto_field()

    class Meta:
        model = Collection
