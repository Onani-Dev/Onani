# -*- coding: utf-8 -*-
# @Author: dirt3009
# @Date:   2022-03-17 20:38:10
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-02 02:00:56
from celery.result import AsyncResult
from flask import request
from Onani.tasks import import_post

from . import main_api, csrf, make_api_response


@main_api.route("/import", methods=["POST"])
@csrf.exempt
def importer_post():
    task = import_post.delay(request.json["url"])
    return make_api_response({"id": task.id})


@main_api.route("/import/result", methods=["GET"])
def import_post_result():
    task: AsyncResult = import_post.AsyncResult(request.args.get("id"))
    return make_api_response({"status": task.state, "result": task.result})
