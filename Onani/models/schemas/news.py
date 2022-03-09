# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 20:03:24
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 20:10:47
from Onani.models import NewsPost

from . import ma


class NewsPostSchema(ma.SQLAlchemyAutoSchema):
    author = ma.auto_field()

    class Meta:
        model = NewsPost
