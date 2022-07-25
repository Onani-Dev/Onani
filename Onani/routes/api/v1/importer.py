# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-18 02:06:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-25 16:46:41
from celery.result import AsyncResult
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import permissions_required
from Onani.models.user.permissions import UserPermissions
from Onani.tasks import import_post

from . import api


class Importer(Resource):
    decorators = [login_required, permissions_required(UserPermissions.IMPORT_POSTS)]

    def post(self):
        args = self._extracted_from_get_2("url")
        task = import_post.delay(args["url"], current_user.id)
        return {"id": task.id}

    def get(self):
        args = self._extracted_from_get_2("id")
        task: AsyncResult = import_post.AsyncResult(args["id"])
        return {"status": task.state, "result": str(task.result)}

    # TODO Rename this here and in `post` and `get`
    def _extracted_from_get_2(self, arg0):
        parser = reqparse.RequestParser()
        parser.add_argument(arg0, location="json", type=str, required=True)
        return parser.parse_args()


api.add_resource(Importer, "/import")
