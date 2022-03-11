# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 21:54:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 03:15:30

from flask import Blueprint
from .. import db, login_manager, csrf

main = Blueprint("main", __name__)
main_api = Blueprint("api", __name__)

admin = Blueprint("admin", __name__)
admin_api = Blueprint("api", __name__)

from . import auth, views, api, errors
