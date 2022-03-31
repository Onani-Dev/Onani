# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 21:54:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-01 02:19:39

from flask import Blueprint

from .. import csrf, db, login_manager

main = Blueprint("main", __name__)
main_api = Blueprint("api", __name__)

admin = Blueprint("admin", __name__)
admin_api = Blueprint("api", __name__)

from . import api, auth, data, errors, views
