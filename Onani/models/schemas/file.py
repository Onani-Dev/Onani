# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:12:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:39:02
from marshmallow import fields
from Onani.models import File

from . import ma


class FileSchema(ma.SQLAlchemyAutoSchema):
    post = ma.auto_field()

    class Meta:
        model = File
