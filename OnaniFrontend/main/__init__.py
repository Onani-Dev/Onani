# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-11 22:36:25
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-12 18:47:45

from flask import Blueprint

from OnaniCore import DatabaseController

onaniDB = DatabaseController("mongodb://localhost:27017/")
main = Blueprint("main", __name__)

from . import api, admin, handlers, login, routes, sockets
