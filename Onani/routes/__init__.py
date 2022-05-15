# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 21:54:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 08:34:32

from flask import Blueprint

from .. import csrf, db, login_manager, limiter
from .api import main_api

main = Blueprint("main", __name__)

admin = Blueprint("admin", __name__)
admin_api = Blueprint("api", __name__)

atom = Blueprint("atom", __name__)
rss = Blueprint("rss", __name__)

from . import auth, data, errors, feed, views
