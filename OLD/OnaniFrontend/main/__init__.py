# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-11 22:36:25
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-14 18:41:24

from flask import Blueprint

from OnaniCore import DatabaseController

onaniDB = DatabaseController("mongodb://localhost:27017/")
main = Blueprint("main", __name__)
main_api = Blueprint("api", __name__)

from . import api, admin, handlers, login, routes, sockets
