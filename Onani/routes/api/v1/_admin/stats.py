# -*- coding: utf-8 -*-
"""Admin dashboard API endpoints — stats, task management, error logs."""
import datetime
import os

from flask import abort, request
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from sqlalchemy import func, or_

from Onani.controllers import permissions_required, role_required
from Onani.models import (
    Ban,
    Collection,
    Error,
    ImportJob,
    Post,
    PostComment,
    PostRating,
    ScheduledImport,
    Tag,
    User,
    UserPermissions,
    UserRoles,
    UserSchema,
)
from Onani.services import enqueue_import_job

from . import api, db


class AdminStats(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        since_24h = now - datetime.timedelta(hours=24)

        rating_counts = {
            "general": Post.query.filter(Post.rating == PostRating.GENERAL).count(),
            "questionable": Post.query.filter(Post.rating == PostRating.QUESTIONABLE).count(),
            "sensitive": Post.query.filter(Post.rating == PostRating.SENSITIVE).count(),
            "explicit": Post.query.filter(Post.rating == PostRating.EXPLICIT).count(),
        }

        import_status_rows = (
            db.session.query(ImportJob.status, func.count(ImportJob.id))
            .group_by(ImportJob.status)
            .all()
        )
        import_status_counts = {status or "UNKNOWN": count for status, count in import_status_rows}
        import_terminal_states = {"SUCCESS", "FAILURE", "REVOKED", "ERROR"}

        active_bans = Ban.query.filter(
            or_(
                Ban.expires.is_(None),
                Ban.expires > now,
            )
        ).count()

        return {
            "posts": Post.query.count(),
            "posts_hidden": Post.query.filter_by(hidden=True).count(),
            "posts_imported": Post.query.filter(Post.imported_from.isnot(None)).count(),
            "posts_with_source": Post.query.filter(Post.source.isnot(None)).count(),
            "posts_tag_request": Post.query.filter(Post.tags.any(Tag.name == "tag_request")).count(),
            "posts_last_24h": Post.query.filter(Post.uploaded_at >= since_24h).count(),
            "ratings": rating_counts,
            "users": User.query.count(),
            "users_deleted": User.query.filter_by(is_deleted=True).count(),
            "users_banned_active": active_bans,
            "users_last_24h": User.query.filter(User.created_at >= since_24h).count(),
            "tags": Tag.query.count(),
            "collections": Collection.query.count(),
            "comments": PostComment.query.count(),
            "comments_last_24h": PostComment.query.filter(PostComment.created_at >= since_24h).count(),
            "errors": Error.query.count(),
            "imports": {
                "total": ImportJob.query.count(),
                "active": sum(
                    count
                    for status, count in import_status_counts.items()
                    if status not in import_terminal_states
                ),
                "queued": import_status_counts.get("QUEUED", 0),
                "success": import_status_counts.get("SUCCESS", 0),
                "failed": import_status_counts.get("FAILURE", 0)
                + import_status_counts.get("ERROR", 0),
                "revoked": import_status_counts.get("REVOKED", 0),
            },
            "scheduled_imports": {
                "total": ScheduledImport.query.count(),
                "enabled": ScheduledImport.query.filter_by(enabled=True).count(),
                "disabled": ScheduledImport.query.filter_by(enabled=False).count(),
            },
        }


class AdminErrors(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=20)
        args = parser.parse_args()

        page = Error.query.order_by(Error.created_at.desc()).paginate(
            page=args["page"], per_page=args["per_page"], error_out=False
        )

        return {
            "data": [
                {
                    "id": str(e.id),
                    "exception_type": e.exception_type,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "traceback": e.traceback,
                }
                for e in page.items
            ],
            "total": page.total,
            "page": page.page,
            "next_page": page.next_num,
            "prev_page": page.prev_num,
        }


class AdminRunTask(Resource):
    decorators = [login_required, role_required(UserRoles.ADMIN)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "task", location="json", type=str, required=True,
            choices=[
                "remove_expired_bans",
                "backfill_video_thumbnails",
                "generate_all_thumbnails",
                "recount_tags",
                "migrate_images",
                "clear_import_queue",
                "restart_celery",
                "deepdanbooru_tag_posts",
                "deepdanbooru_tag_all_posts",
            ],
        )
        args = parser.parse_args()
        task_name = args["task"]

        if task_name == "clear_import_queue":
            from Onani.models.import_job import ImportJob
            count = (
                ImportJob.query
                .filter_by(status="QUEUED")
                .update({"status": "REVOKED", "finished_at": datetime.datetime.now(datetime.timezone.utc)})
            )
            db.session.commit()
            return {"message": f"Cleared {count} queued import job(s)."}

        if task_name == "restart_celery":
            # ext.celery is None at module import time — it is only set after
            # init_app() runs.  Retrieve the live Celery app from the Flask
            # extension registry instead.
            from flask import current_app as _app
            _ext = _app.extensions.get("flask-celeryext")
            if _ext is None or _ext.celery is None:
                return {"message": "Celery app not found."}, 500
            replies = _ext.celery.control.broadcast("pool_restart", reply=True, timeout=5)
            if not replies:
                return {"message": "No Celery workers responded (queue may still be running)."}
            errors = [
                f"{worker}: {list(r.values())[0].get('error', '')}"
                for reply in replies
                for worker, r in reply.items()
                if isinstance(list(r.values())[0], dict) and list(r.values())[0].get("error")
            ]
            if errors:
                return {"message": f"pool_restart failed: {'; '.join(errors)}"}, 500
            return {"message": f"Sent pool_restart to {len(replies)} Celery worker(s)."}

        if task_name == "remove_expired_bans":
            from Onani.cron.tasks import remove_expired_bans
            remove_expired_bans()
            return {"message": "Task 'remove_expired_bans' completed."}

        if task_name == "migrate_images":
            import shutil
            from flask import current_app as _app
            from Onani.services.files import shard_path
            images_dir = _app.config.get("IMAGES_DIR", "/images")
            moved = skipped = failed = 0
            for entry in os.scandir(images_dir):
                if not entry.is_file():
                    continue
                filename = entry.name
                if len(filename) < 2 or not filename[0:2].isalnum():
                    continue
                dest = shard_path(images_dir, filename)
                if os.path.exists(dest):
                    try:
                        os.remove(entry.path)
                        skipped += 1
                    except OSError:
                        skipped += 1
                    continue
                try:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.move(entry.path, dest)
                    moved += 1
                except Exception as exc:
                    failed += 1
            return {"message": f"migrate-images completed — moved:{moved} skipped:{skipped} failed:{failed}"}

        if task_name == "backfill_video_thumbnails":
            from Onani.services.files import create_video_thumbnail, shard_path, ensure_shard_dir
            from flask import current_app
            import os
            images_dir = current_app.config["IMAGES_DIR"]
            VIDEO_FORMATS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
            videos = Post.query.filter(Post.file_type.in_(list(VIDEO_FORMATS))).all()
            ok = skipped = failed = 0
            for post in videos:
                stem = post.filename.rsplit(".", 1)[0]
                thumb_name = f"{stem}.jpg"
                thumb = shard_path(images_dir, thumb_name)
                if os.path.exists(thumb):
                    skipped += 1
                    continue
                src = shard_path(images_dir, post.filename)
                if not os.path.exists(src):
                    failed += 1
                    continue
                dest = ensure_shard_dir(images_dir, thumb_name)
                if create_video_thumbnail(src, dest):
                    ok += 1
                else:
                    failed += 1
            return {"message": f"Backfill complete — generated:{ok} skipped:{skipped} failed:{failed}"}

        if task_name == "generate_all_thumbnails":
            from Onani.tasks.thumbnails import generate_all_thumbnails as _gen_thumbs
            result = _gen_thumbs.apply_async()
            return {
                "message": "Thumbnail generation queued.",
                "task_id": result.id,
            }

        if task_name == "recount_tags":
            from Onani.models import Tag
            tags = Tag.query.all()
            for tag in tags:
                tag.recount_posts()
            db.session.commit()
            return {"message": f"Recounted {len(tags)} tags."}

        if task_name in ("deepdanbooru_tag_posts", "deepdanbooru_tag_all_posts"):
            from flask import current_app as _app

            from Onani.services.deepdanbooru import get_deepdanbooru_status
            from Onani.tasks.deepdanbooru import (
                deepdanbooru_tag_all_posts,
                deepdanbooru_tag_tag_request_posts,
            )

            status = get_deepdanbooru_status(_app.config)
            if not status["available"]:
                return {"message": status["reason"] or "DeepDanbooru is unavailable."}, 400

            if task_name == "deepdanbooru_tag_all_posts":
                result = deepdanbooru_tag_all_posts.apply_async()
                queued_message = "DeepDanbooru all-post tagging queued."
            else:
                result = deepdanbooru_tag_tag_request_posts.apply_async()
                queued_message = "DeepDanbooru tag-request tagging queued."

            return {
                "message": queued_message,
                "task_id": result.id,
            }

        return {"message": "Unknown task."}, 400


class AdminUsers(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=30)
        parser.add_argument("q", location="args", type=str, default=None)
        args = parser.parse_args()

        query = User.query
        if args["q"]:
            query = query.filter(User.username.ilike(f"%{args['q']}%"))
        query = query.order_by(User.id.asc())

        page = query.paginate(page=args["page"], per_page=args["per_page"], error_out=False)
        return {
            "data": UserSchema(many=True).dump(page.items),
            "total": page.total,
            "next_page": page.next_num,
            "prev_page": page.prev_num,
        }

    def post(self):
        """Create a new user (admin only)."""
        if not current_user.has_role(UserRoles.ADMIN):
            abort(403)

        parser = reqparse.RequestParser()
        parser.add_argument("username", location="json", type=str, required=True)
        parser.add_argument("email",    location="json", type=str, required=False)
        parser.add_argument("password", location="json", type=str, required=True)
        parser.add_argument(
            "role", location="json", type=str, default="MEMBER",
            choices=["MEMBER", "HELPER", "MODERATOR", "ADMIN", "OWNER"],
        )
        args = parser.parse_args()

        if User.query.filter_by(username=args["username"]).first():
            return {"message": "Username already taken."}, 409

        user = User(username=args["username"], email=args["email"] or None)
        user.set_password(args["password"])
        user.role = UserRoles[args["role"]]
        db.session.add(user)
        db.session.commit()
        return UserSchema().dump(user), 201

    def put(self):
        if not current_user.has_role(UserRoles.ADMIN):
            abort(403)

        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        parser.add_argument(
            "role", location="json", type=str, required=True,
            choices=["MEMBER", "HELPER", "MODERATOR", "ADMIN", "OWNER"],
        )
        args = parser.parse_args()

        user = User.query.filter_by(id=args["id"]).first_or_404()
        if user.id == current_user.id:
            abort(400)
        if user.has_role(UserRoles.OWNER) and not current_user.has_role(UserRoles.OWNER):
            abort(403)

        user.role = UserRoles[args["role"]]
        db.session.commit()
        return UserSchema().dump(user)

    def delete(self):
        if not current_user.has_role(UserRoles.ADMIN):
            abort(403)

        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        args = parser.parse_args()

        user = User.query.filter_by(id=args["id"]).first_or_404()
        if user.id == current_user.id or user.has_role(UserRoles.OWNER):
            abort(403)

        db.session.delete(user)
        db.session.commit()
        return {}, 204


class AdminImports(Resource):
    """DB-backed import history for MODERATOR+ admins.

    The frontend now uses the role-aware ``GET /imports`` endpoint directly.
    This resource is kept for backward-compat and adds the Celery active-task
    overlay on top of the DB view.
    """
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        from Onani.models.import_job import ImportJob

        parser = reqparse.RequestParser()
        parser.add_argument("page",     location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=20)
        args = parser.parse_args()
        per_page = max(1, min(args["per_page"], 50))

        page = (
            ImportJob.query
            .order_by(ImportJob.created_at.desc())
            .paginate(page=args["page"], per_page=per_page, error_out=False)
        )

        tasks = []
        for j in page.items:
            tasks.append({
                "id":          j.task_id,
                "url":         j.url,
                "status":      j.status,
                "result":      j.result,
                "created_at":  j.created_at.isoformat() if j.created_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "user": {
                    "id":       j.user.id,
                    "username": j.user.username,
                } if j.user else None,
            })

        return {
            "tasks": tasks,
            "total": page.total,
            "page":  page.page,
            "pages": page.pages,
        }


class AdminCeleryLogs(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    LOG_PATH = "/logs/celery.log"
    MAX_LINES = 500

    def get(self):
        import os
        parser = reqparse.RequestParser()
        parser.add_argument("lines", location="args", type=int, default=100)
        args = parser.parse_args()
        n = max(1, min(args["lines"], self.MAX_LINES))

        if not os.path.exists(self.LOG_PATH):
            return {"lines": [], "available": False}

        try:
            # Efficient tail without loading the whole file into memory
            with open(self.LOG_PATH, "rb") as f:
                # Read up to 256 KB from the end
                f.seek(0, 2)
                size = f.tell()
                read_size = min(size, 256 * 1024)
                f.seek(-read_size, 2)
                chunk = f.read()
            raw_lines = chunk.decode("utf-8", errors="replace").splitlines()
            tail = raw_lines[-n:]
            return {"lines": tail, "available": True}
        except OSError as e:
            return {"lines": [], "available": False, "error": str(e)}


class AdminFlaskLogs(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    LOG_PATHS = {
        "access": "/logs/onani.access.log",
        "error":  "/logs/onani.error.log",
    }
    MAX_LINES = 500

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("type",  location="args", type=str, default="error",
                            choices=["access", "error"])
        parser.add_argument("lines", location="args", type=int, default=100)
        args = parser.parse_args()
        n = max(1, min(args["lines"], self.MAX_LINES))

        log_path = self.LOG_PATHS[args["type"]]
        if not os.path.exists(log_path):
            return {"lines": [], "available": False}

        try:
            with open(log_path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                read_size = min(size, 256 * 1024)
                f.seek(-read_size, 2)
                chunk = f.read()
            raw_lines = chunk.decode("utf-8", errors="replace").splitlines()
            return {"lines": raw_lines[-n:], "available": True}
        except OSError as e:
            return {"lines": [], "available": False, "error": str(e)}


class AdminScheduledImports(Resource):
    decorators = [login_required, role_required(UserRoles.ADMIN)]

    VALID_INTERVALS = {30, 60, 120, 360, 720, 1440, 2880, 10080}

    def _serialize(self, task):
        return {
            "id": task.id,
            "label": task.label,
            "url": task.url,
            "interval_minutes": task.interval_minutes,
            "enabled": task.enabled,
            "has_cookies": bool(task.cookies),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "last_run_status": task.last_run_status,
            "last_error": task.last_error,
            "creator_id": task.creator_id,
            # Note: cookies are never returned to the client
        }

    def get(self):
        tasks = ScheduledImport.query.order_by(ScheduledImport.id.asc()).all()
        return {"data": [self._serialize(t) for t in tasks]}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("url",              location="json", type=str, required=True)
        parser.add_argument("label",            location="json", type=str, default=None)
        parser.add_argument("interval_minutes", location="json", type=int, required=True)
        parser.add_argument("enabled",          location="json", type=bool, default=True)
        parser.add_argument("cookies",          location="json", type=str, default=None)
        args = parser.parse_args()

        if args["interval_minutes"] not in self.VALID_INTERVALS:
            return {"message": f"interval_minutes must be one of {sorted(self.VALID_INTERVALS)}."}, 400

        task = ScheduledImport(
            url=args["url"].strip(),
            label=args["label"] or None,
            interval_minutes=args["interval_minutes"],
            enabled=args["enabled"],
            cookies=args["cookies"] or None,
            creator_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        return self._serialize(task), 201

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id",               location="json", type=int, required=True)
        parser.add_argument("url",              location="json", type=str, default=None)
        parser.add_argument("label",            location="json", type=str, default=None)
        parser.add_argument("interval_minutes", location="json", type=int, default=None)
        parser.add_argument("enabled",          location="json", type=bool, default=None)
        # Cookies are handled via raw JSON payload below so we can distinguish
        # between omitted and explicit null/empty values.
        parser.add_argument("cookies",          location="json", type=str, default=None)
        args = parser.parse_args()
        payload = request.get_json(silent=True) or {}

        task = ScheduledImport.query.filter_by(id=args["id"]).first_or_404()

        if args["url"] is not None:
            task.url = args["url"].strip()
        if args["label"] is not None:
            task.label = args["label"] or None
        if args["interval_minutes"] is not None:
            if args["interval_minutes"] not in self.VALID_INTERVALS:
                return {"message": f"interval_minutes must be one of {sorted(self.VALID_INTERVALS)}."}, 400
            task.interval_minutes = args["interval_minutes"]
        if args["enabled"] is not None:
            task.enabled = args["enabled"]

        # cookies: explicit empty string clears it; non-empty string sets it
        if "cookies" in payload:
            raw_cookies = args["cookies"]
            task.cookies = raw_cookies.strip() if raw_cookies else None

        db.session.commit()
        return self._serialize(task)

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        args = parser.parse_args()
        task = ScheduledImport.query.filter_by(id=args["id"]).first_or_404()
        db.session.delete(task)
        db.session.commit()
        return {}, 204


class AdminScheduledImportRun(Resource):
    decorators = [login_required, role_required(UserRoles.ADMIN)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        args = parser.parse_args()

        task = ScheduledImport.query.filter_by(id=args["id"]).first_or_404()
        try:
            task_id, queued = enqueue_import_job(task.url, task.creator_id or 1, task.cookies)
            task.last_run_at = datetime.datetime.now(datetime.timezone.utc)
            task.last_run_status = "QUEUED" if queued else "DISPATCHED"
            task.last_error = None
            db.session.commit()
            return {"message": "Task queued." if queued else "Task dispatched.", "task_id": task_id, "queued": queued}
        except Exception as exc:
            task.last_run_at = datetime.datetime.now(datetime.timezone.utc)
            task.last_run_status = "FAILED"
            task.last_error = str(exc)
            db.session.commit()
            return {"message": "Failed to dispatch scheduled import."}, 500


api.add_resource(AdminStats, "/admin/stats")
api.add_resource(AdminErrors, "/admin/errors")
api.add_resource(AdminRunTask, "/admin/tasks")
api.add_resource(AdminUsers, "/admin/users")
api.add_resource(AdminImports, "/admin/imports")
api.add_resource(AdminCeleryLogs, "/admin/celery-logs")
api.add_resource(AdminFlaskLogs, "/admin/flask-logs")
api.add_resource(AdminScheduledImports, "/admin/scheduled-imports")
api.add_resource(AdminScheduledImportRun, "/admin/scheduled-imports/run")
