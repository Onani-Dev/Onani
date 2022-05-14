# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:42:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 08:59:06

from flask import Blueprint

from .. import csrf
from . import v1

main_api = Blueprint("api", __name__)
main_api.register_blueprint(v1.api_v1)
