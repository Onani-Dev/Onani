# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 21:54:05
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-23 16:19:51

from flask import Blueprint

from .. import csrf, db, login_manager

main = Blueprint("main", __name__)
main_api = Blueprint("api", __name__)

admin = Blueprint("admin", __name__)
admin_api = Blueprint("api", __name__)

atom = Blueprint("atom", __name__)
rss = Blueprint("rss", __name__)

from . import api, auth, data, errors, views, feed
