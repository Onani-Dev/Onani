# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-18 02:06:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 14:48:20
import datetime

from celery.result import AsyncResult
from flask import abort, session
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers.crypto import decrypt_cookies
from Onani.models import ImportJob, UserRoles
from Onani.services import enqueue_import_job
from Onani.tasks import import_post

from . import api, db


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

        task_id, queued = enqueue_import_job(args["url"], current_user.id, cookies_content)
        return {"id": task_id, "queued": queued}

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="args", type=str, required=True)
        args = parser.parse_args()

        # Check the DB record first so we can return QUEUED status for jobs
        # that haven't been dispatched to Celery yet.
        job_rec_check = ImportJob.query.filter_by(task_id=args["id"]).first()
        if job_rec_check and job_rec_check.status == "QUEUED":
            return {"status": "QUEUED", "result": None, "meta": None}

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

        # Sync terminal state back to the ImportJob record
        if state in ("SUCCESS", "FAILURE", "REVOKED"):
            job_rec = ImportJob.query.filter_by(task_id=args["id"]).first()
            if job_rec and job_rec.status not in ("SUCCESS", "FAILURE", "REVOKED"):
                job_rec.status = state
                job_rec.result = result
                job_rec.finished_at = datetime.datetime.now(datetime.timezone.utc)
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        return {"status": state, "result": result, "meta": meta}

    @login_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="args", type=str, required=True)
        args = parser.parse_args()

        # Permission check: own job or MODERATOR+
        job_rec = ImportJob.query.filter_by(task_id=args["id"]).first()
        if job_rec and job_rec.user_id != current_user.id:
            if not current_user.has_role(UserRoles.MODERATOR):
                abort(403)

        # QUEUED jobs haven't been dispatched to Celery yet — just cancel in DB.
        if job_rec and job_rec.status == "QUEUED":
            job_rec.status = "REVOKED"
            job_rec.finished_at = datetime.datetime.now(datetime.timezone.utc)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            return {"message": "Task revoked."}

        task: AsyncResult = import_post.AsyncResult(args["id"])
        task.revoke(terminate=True, signal="SIGKILL")

        if job_rec:
            job_rec.status = "REVOKED"
            job_rec.finished_at = datetime.datetime.now(datetime.timezone.utc)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        return {"message": "Task revoked."}


class ImporterList(Resource):
    """List import jobs — all jobs for MODERATOR+, own jobs otherwise."""

    decorators = [login_required]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page",     location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=20)
        parser.add_argument("mine",     location="args", type=int, default=0)
        args = parser.parse_args()

        per_page = max(1, min(args["per_page"], 50))

        # MODERATOR+ see all jobs unless ?mine=1 is set (e.g. from ImportView)
        is_admin = current_user.has_role(UserRoles.MODERATOR) and not args["mine"]

        query = ImportJob.query.order_by(ImportJob.created_at.desc())
        if not is_admin:
            query = query.filter_by(user_id=current_user.id)

        page = query.paginate(page=args["page"], per_page=per_page, error_out=False)

        data = []
        for j in page.items:
            entry = {
                "id":          j.task_id,
                "url":         j.url,
                "status":      j.status,
                "result":      j.result,
                "created_at":  j.created_at.isoformat() if j.created_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            }
            if is_admin:
                entry["user"] = {
                    "id":       j.user.id,
                    "username": j.user.username,
                } if j.user else None
            data.append(entry)

        return {
            "data":  data,
            "total": page.total,
            "page":  page.page,
            "pages": page.pages,
        }


api.add_resource(Importer,     "/import")
api.add_resource(ImporterList, "/imports")

