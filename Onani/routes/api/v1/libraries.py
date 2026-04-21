# -*- coding: utf-8 -*-
"""REST endpoints for managing external libraries.

All mutating operations require ADMINISTRATION permission.
Read-only access (GET) requires at least MODERATOR role.
"""

import datetime
import uuid

from celery.result import AsyncResult
from flask import abort
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse

from Onani.controllers.permissions import permissions_required
from Onani.controllers.role import role_required
from Onani.models import ExternalLibrary, ExternalLibraryFile, UserPermissions, UserRoles
from Onani.tasks import scan_library

from . import api, db


def _library_dict(lib: ExternalLibrary) -> dict:
    return {
        "id": lib.id,
        "name": lib.name,
        "path": lib.path,
        "enabled": lib.enabled,
        "default_rating": lib.default_rating,
        "default_tags": lib.default_tags or "",
        "owner_id": lib.owner_id,
        "created_at": lib.created_at.isoformat() if lib.created_at else None,
        "last_scan_at": lib.last_scan_at.isoformat() if lib.last_scan_at else None,
        "last_scan_status": lib.last_scan_status,
        "last_scan_task_id": lib.last_scan_task_id,
        "file_count": lib.file_count,
        "imported_count": lib.imported_count,
    }


class LibraryList(Resource):
    """GET /libraries — list all libraries (MODERATOR+)
    POST /libraries — create a library (ADMINISTRATION permission)
    """

    decorators = [login_required]

    @role_required(UserRoles.MODERATOR)
    def get(self):
        libs = ExternalLibrary.query.order_by(ExternalLibrary.id).all()
        return [_library_dict(lib) for lib in libs]

    @permissions_required(UserPermissions.ADMINISTRATION)
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", location="json", type=str, required=True)
        parser.add_argument("path", location="json", type=str, required=True)
        parser.add_argument("enabled", location="json", type=bool, default=True)
        parser.add_argument("default_rating", location="json", type=str, default="q")
        parser.add_argument("default_tags", location="json", type=str, default="")
        args = parser.parse_args()

        # Normalise and basic-validate the path.
        path = args["path"].strip()
        if not path:
            abort(400, description="path must not be empty.")

        import os
        path = os.path.normpath(path)
        if not os.path.isabs(path):
            abort(400, description="path must be an absolute filesystem path.")

        valid_ratings = {"g", "q", "e"}
        if args["default_rating"] not in valid_ratings:
            abort(400, description="default_rating must be one of: g, q, e.")

        lib = ExternalLibrary(
            name=args["name"].strip(),
            path=path,
            enabled=args["enabled"],
            default_rating=args["default_rating"],
            default_tags=args["default_tags"].strip() or None,
            owner_id=current_user.id,
        )
        db.session.add(lib)
        db.session.commit()
        return _library_dict(lib), 201


class LibraryDetail(Resource):
    """GET/PUT/DELETE /libraries/<id> — manage a single library."""

    decorators = [login_required]

    @role_required(UserRoles.MODERATOR)
    def get(self, library_id: int):
        lib = ExternalLibrary.query.get_or_404(library_id)
        return _library_dict(lib)

    @permissions_required(UserPermissions.ADMINISTRATION)
    def put(self, library_id: int):
        lib = ExternalLibrary.query.get_or_404(library_id)

        parser = reqparse.RequestParser()
        parser.add_argument("name", location="json", type=str)
        parser.add_argument("path", location="json", type=str)
        parser.add_argument("enabled", location="json", type=bool)
        parser.add_argument("default_rating", location="json", type=str)
        parser.add_argument("default_tags", location="json", type=str)
        args = parser.parse_args()

        import os

        if args["name"] is not None:
            lib.name = args["name"].strip()
        if args["path"] is not None:
            path = os.path.normpath(args["path"].strip())
            if not os.path.isabs(path):
                abort(400, description="path must be an absolute filesystem path.")
            lib.path = path
        if args["enabled"] is not None:
            lib.enabled = args["enabled"]
        if args["default_rating"] is not None:
            valid_ratings = {"g", "q", "e"}
            if args["default_rating"] not in valid_ratings:
                abort(400, description="default_rating must be one of: g, q, e.")
            lib.default_rating = args["default_rating"]
        if args["default_tags"] is not None:
            lib.default_tags = args["default_tags"].strip() or None

        db.session.commit()
        return _library_dict(lib)

    @permissions_required(UserPermissions.ADMINISTRATION)
    def delete(self, library_id: int):
        lib = ExternalLibrary.query.get_or_404(library_id)
        db.session.delete(lib)
        db.session.commit()
        return {"message": "Library deleted."}


class LibraryScan(Resource):
    """POST /libraries/<id>/scan — trigger a scan.
    GET  /libraries/<id>/scan — get current scan status.
    """

    decorators = [login_required]

    @role_required(UserRoles.MODERATOR)
    def get(self, library_id: int):
        lib = ExternalLibrary.query.get_or_404(library_id)
        result = None
        meta = None
        state = lib.last_scan_status or "IDLE"

        if lib.last_scan_task_id:
            task: AsyncResult = scan_library.AsyncResult(lib.last_scan_task_id)
            try:
                if task.state in ("PENDING", "PROGRESS", "SUCCESS", "FAILURE"):
                    state = task.state
                    raw = task.result
                    result = raw if isinstance(raw, dict) else str(raw) if raw else None
                    meta = task.info if task.state == "PROGRESS" and isinstance(task.info, dict) else None
            except Exception:
                pass

        return {
            "library_id": library_id,
            "task_id": lib.last_scan_task_id,
            "status": state,
            "last_scan_at": lib.last_scan_at.isoformat() if lib.last_scan_at else None,
            "result": result,
            "meta": meta,
        }

    @permissions_required(UserPermissions.ADMINISTRATION)
    def post(self, library_id: int):
        lib = ExternalLibrary.query.get_or_404(library_id)

        if not lib.enabled:
            abort(400, description="Library is disabled.")

        # Prevent concurrent scans.
        if lib.last_scan_status == "SCANNING" and lib.last_scan_task_id:
            task: AsyncResult = scan_library.AsyncResult(lib.last_scan_task_id)
            try:
                if task.state in ("PENDING", "STARTED"):
                    return {
                        "message": "A scan is already running.",
                        "task_id": lib.last_scan_task_id,
                    }, 409
            except Exception:
                pass

        task_id = str(uuid.uuid4())
        lib.last_scan_task_id = task_id
        lib.last_scan_status = "SCANNING"
        db.session.commit()

        scan_library.apply_async(args=[library_id], task_id=task_id)

        return {"message": "Scan started.", "task_id": task_id}, 202


class LibraryFileList(Resource):
    """GET /libraries/<id>/files — paginated list of tracked files."""

    decorators = [login_required, role_required(UserRoles.MODERATOR)]

    def get(self, library_id: int):
        ExternalLibrary.query.get_or_404(library_id)

        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=50)
        parser.add_argument("status", location="args", type=str, default=None)
        args = parser.parse_args()

        per_page = max(1, min(args["per_page"], 200))
        query = (
            ExternalLibraryFile.query
            .filter_by(library_id=library_id)
            .order_by(ExternalLibraryFile.file_path)
        )
        if args["status"]:
            query = query.filter_by(status=args["status"].upper())

        page = query.paginate(page=args["page"], per_page=per_page, error_out=False)

        return {
            "data": [
                {
                    "id": f.id,
                    "file_path": f.file_path,
                    "sha256_hash": f.sha256_hash,
                    "status": f.status,
                    "post_id": f.post_id,
                    "error": f.error,
                    "first_seen_at": f.first_seen_at.isoformat() if f.first_seen_at else None,
                    "last_seen_at": f.last_seen_at.isoformat() if f.last_seen_at else None,
                    "imported_at": f.imported_at.isoformat() if f.imported_at else None,
                }
                for f in page.items
            ],
            "total": page.total,
            "page": page.page,
            "pages": page.pages,
        }


api.add_resource(LibraryList,     "/libraries")
api.add_resource(LibraryDetail,   "/libraries/<int:library_id>")
api.add_resource(LibraryScan,     "/libraries/<int:library_id>/scan")
api.add_resource(LibraryFileList, "/libraries/<int:library_id>/files")
