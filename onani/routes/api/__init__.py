# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:42:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-26 14:55:44

from flask import Blueprint

from .. import csrf, limiter, db
from .v1 import api_v1

main_api = Blueprint("api", __name__)
main_api.register_blueprint(api_v1)
