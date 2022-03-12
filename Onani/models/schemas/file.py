# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:12:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 13:44:42
from marshmallow import fields
from Onani.models import File

from . import ma


class FileSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = File
