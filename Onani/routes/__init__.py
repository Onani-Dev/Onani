# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 21:54:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-11-08 22:04:53

from flask import Blueprint
from .. import db

main = Blueprint("main", __name__)
api = Blueprint("api", __name__)

from . import views