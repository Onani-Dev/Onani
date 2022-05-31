# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:13:10
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:11:30
from marshmallow import fields
from Onani.models import Ban

from . import ma


class BanSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ban
        exclude = ("id",)
