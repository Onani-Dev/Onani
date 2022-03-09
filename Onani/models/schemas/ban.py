# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:13:10
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:38:47
from marshmallow import fields
from Onani.models import Ban

from . import ma


class BanSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ban
