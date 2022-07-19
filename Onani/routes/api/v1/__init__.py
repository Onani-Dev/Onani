# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-14 07:44:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-19 13:09:25
from flask import Blueprint
from flask_restful import Api

from .. import csrf, limiter, db

api_v1 = Blueprint("v1", __name__, url_prefix="/v1")

api = Api(api_v1, decorators=[csrf.exempt])

from .comments import *
from .importer import *
from .index import *
from .news import *
from .posts import *
from .tags import *
from ._admin import *
