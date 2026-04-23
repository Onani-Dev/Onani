# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-15 04:26:17
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 08:11:31
from flask import request
from flask_login import current_user
from flask_restful import Resource
from . import api


class Index(Resource):
    def get(self):
        return {
            "version": request.blueprint,
            "user": None if current_user.is_anonymous else current_user.username,
            "ip": request.remote_addr,
        }


api.add_resource(Index, "/")
