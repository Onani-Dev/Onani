# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:14:09
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:11:26
from marshmallow import fields
from Onani.models import Collection

from . import ma


class CollectionSchema(ma.SQLAlchemyAutoSchema):
    posts = ma.Nested("PostSchema", many=True)

    class Meta:
        model = Collection
