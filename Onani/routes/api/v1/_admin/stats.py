# -*- coding: utf-8 -*-
"""Admin dashboard API endpoints — stats, task management, error logs."""
from flask import abort
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse

from Onani.controllers import permissions_required, role_required
from Onani.models import (
    Collection,
    Error,
    Post,
    Tag,
    User,
    UserPermissions,
    UserRoles,
    UserSchema,
)

from . import api, db


class AdminStats(Resource):
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        return {
            "posts": Post.query.count(),
            "users": User.query.count(),
            "tags": Tag.query.count(),
            "collections": Collection.query.count(),
            "errors": Error.query.count(),
        }


class AdminErrors(Resource):
    decorators = [
        login_required,
        permissions_required(UserPermissions.VIEW_LOGS),
    ]

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
            choices=["remove_expired_bans", "backfill_video_thumbnails", "recount_tags"],
        )
        args = parser.parse_args()
        task_name = args["task"]

        if task_name == "remove_expired_bans":
            from Onani.cron.tasks import remove_expired_bans
            remove_expired_bans()
            return {"message": "Task 'remove_expired_bans' completed."}

        if task_name == "backfill_video_thumbnails":
            from Onani.services.files import create_video_thumbnail
            from flask import current_app
            import os
            images_dir = current_app.config["IMAGES_DIR"]
            VIDEO_FORMATS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}
            videos = Post.query.filter(Post.file_type.in_(list(VIDEO_FORMATS))).all()
            ok = skipped = failed = 0
            for post in videos:
                stem = post.filename.rsplit(".", 1)[0]
                thumb = os.path.join(images_dir, f"{stem}.jpg")
                if os.path.exists(thumb):
                    skipped += 1
                    continue
                src = os.path.join(images_dir, post.filename)
                if not os.path.exists(src):
                    failed += 1
                    continue
                if create_video_thumbnail(src, thumb):
                    ok += 1
                else:
                    failed += 1
            return {"message": f"Backfill complete — generated:{ok} skipped:{skipped} failed:{failed}"}

        if task_name == "recount_tags":
            from Onani.models import Tag
            tags = Tag.query.all()
            for tag in tags:
                tag.recount_posts()
            db.session.commit()
            return {"message": f"Recounted {len(tags)} tags."}

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
            choices=["MEMBER", "ARTIST", "PREMIUM", "HELPER", "MODERATOR", "ADMIN"],
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
            choices=["MEMBER", "ARTIST", "PREMIUM", "HELPER", "MODERATOR", "ADMIN"],
        )
        args = parser.parse_args()

        user = User.query.filter_by(id=args["id"]).first_or_404()
        if user.id == current_user.id:
            abort(400)
        if user.has_role(UserRoles.OWNER):
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
    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self):
        try:
            from Onani import ext
            inspector = ext.celery.control.inspect(timeout=1.0)
            active = inspector.active() or {}
        except Exception:
            active = {}

        tasks = []
        for worker, worker_tasks in active.items():
            for t in worker_tasks:
                name = t.get("name", "")
                if "import_post" in name:
                    args = t.get("args", [])
                    tasks.append({
                        "id": t["id"],
                        "url": args[0] if args else None,
                        "worker": worker,
                    })

        return {"tasks": tasks}


api.add_resource(AdminStats, "/admin/stats")
api.add_resource(AdminErrors, "/admin/errors")
api.add_resource(AdminRunTask, "/admin/tasks")
api.add_resource(AdminUsers, "/admin/users")
api.add_resource(AdminImports, "/admin/imports")
