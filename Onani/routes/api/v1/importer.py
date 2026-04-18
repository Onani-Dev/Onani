# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-18 02:06:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 14:48:20
from celery.result import AsyncResult
from flask import session
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers.crypto import decrypt_cookies
from Onani.tasks import import_post

from . import api


class Importer(Resource):

    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("url", location="json", type=str, required=True)
        args = parser.parse_args()

        # Attempt to decrypt cookies if the user has them stored
        cookies_content = None
        settings = current_user.settings
        if settings and settings.encrypted_cookies and settings.cookies_salt:
            pw = session.get("_cookie_pw")
            if pw:
                try:
                    cookies_content = decrypt_cookies(
                        settings.encrypted_cookies,
                        settings.cookies_salt,
                        pw,
                    ).decode("utf-8", errors="replace")
                except Exception:
                    pass  # wrong key / corrupt — import without cookies

        task = import_post.delay(args["url"], current_user.id, cookies_content)
        return {"id": task.id}

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="args", type=str, required=True)
        args = parser.parse_args()
        task: AsyncResult = import_post.AsyncResult(args["id"])
        try:
            state = task.state
            raw = task.result
            result = raw if isinstance(raw, dict) else str(raw) if raw else None
            meta = task.info if state == "PROGRESS" and isinstance(task.info, dict) else None
        except Exception:
            state = "PENDING"
            result = None
            meta = None
        return {"status": state, "result": result, "meta": meta}


api.add_resource(Importer, "/import")
