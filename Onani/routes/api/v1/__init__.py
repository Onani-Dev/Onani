# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-14 07:44:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 12:51:09
from flask import Blueprint
from flask_restful import Api

from .. import csrf, limiter, db

api_v1 = Blueprint("v1", __name__, url_prefix="/v1")

# Auth is enforced per-resource via login_required / permissions_required decorators.
# A global auth wrapper would incorrectly block public read endpoints.
api = Api(api_v1, decorators=[csrf.exempt])

from .auth import *
from .collections import *
from .comments import *
from .importer import *
from .index import *
from .news import *
from .posts import *
from .profile import *
from .tags import *
from .users import *
from ._admin import *
