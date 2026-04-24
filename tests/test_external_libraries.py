# -*- coding: utf-8 -*-
"""Tests for the external libraries API and scan task."""
import json
import os
import tempfile

import pytest


class TestLibraryAPI:
    """CRUD and permissions for /api/v1/libraries."""

    def test_list_requires_login(self, client):
        resp = client.get("/api/v1/libraries")
        assert resp.status_code == 401

    def test_list_requires_moderator(self, client, make_user, app):
        with app.app_context():
            user = make_user(username="lib_member", password="testpassword")
            login_id = user.login_id
        with client.session_transaction() as sess:
            sess["_user_id"] = login_id
            sess["_fresh"] = True
        resp = client.get("/api/v1/libraries")
        assert resp.status_code == 403

    def test_list_as_admin(self, admin_client, app):
        client, admin = admin_client
        resp = client.get("/api/v1/libraries")
        assert resp.status_code == 200
        assert isinstance(json.loads(resp.data), list)

    def test_create_requires_admin(self, logged_in_client, app):
        client, user = logged_in_client
        resp = client.post(
            "/api/v1/libraries",
            json={"name": "Test", "path": "/tmp/test"},
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_create_library(self, admin_client, app):
        client, admin = admin_client
        with tempfile.TemporaryDirectory() as tmpdir:
            resp = client.post(
                "/api/v1/libraries",
                json={"name": "My Library", "path": tmpdir, "recursive": False, "default_rating": "g", "default_tags": "foo bar"},
                content_type="application/json",
            )
            assert resp.status_code == 201
            data = json.loads(resp.data)
            assert data["name"] == "My Library"
            assert data["path"] == tmpdir
            assert data["recursive"] is False
            assert data["default_rating"] == "g"
            assert data["default_tags"] == "foo bar"
            assert data["owner_id"] == admin.id

    def test_disable_library_hides_linked_posts(self, admin_client, app, db):
        from onani.models import ExternalLibrary, ExternalLibraryFile, Post
        import datetime

        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="HideLib", path="/tmp/hidelib", owner_id=admin.id)
            db.session.add(lib)
            db.session.flush()

            post = Post(
                uploader_id=admin.id,
                filename="hidelib-post.png",
                sha256_hash="hidelibsha256",
                md5_hash="hidelibmd5",
                width=1,
                height=1,
                filesize=64,
                file_type="png",
                original_filename="hidelib-post.png",
            )
            db.session.add(post)
            db.session.flush()

            rec = ExternalLibraryFile(
                library_id=lib.id,
                file_path="/tmp/hidelib/a.png",
                status="IMPORTED",
                post_id=post.id,
                first_seen_at=datetime.datetime.utcnow(),
                last_seen_at=datetime.datetime.utcnow(),
            )
            db.session.add(rec)
            db.session.commit()

            resp = client.put(
                f"/api/v1/libraries/{lib.id}",
                json={"enabled": False},
                content_type="application/json",
            )
            assert resp.status_code == 200

            db.session.expire_all()
            post_fresh = Post.query.get(post.id)
            assert post_fresh.hidden is True

    def test_create_library_relative_path_rejected(self, admin_client, app):
        client, admin = admin_client
        resp = client.post(
            "/api/v1/libraries",
            json={"name": "Bad", "path": "relative/path"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_library_invalid_rating_rejected(self, admin_client, app):
        client, admin = admin_client
        resp = client.post(
            "/api/v1/libraries",
            json={"name": "Bad", "path": "/tmp/something", "default_rating": "z"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_library(self, admin_client, app):
        from onani.models import ExternalLibrary
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="GetMe", path="/tmp/getme", owner_id=admin.id)
            from onani import db as _db
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.get(f"/api/v1/libraries/{lib_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["id"] == lib_id
        assert data["name"] == "GetMe"

    def test_get_library_not_found(self, admin_client, app):
        client, _ = admin_client
        resp = client.get("/api/v1/libraries/999999")
        assert resp.status_code == 404

    def test_update_library(self, admin_client, app):
        from onani.models import ExternalLibrary
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="OldName", path="/tmp/upd", owner_id=admin.id)
            from onani import db as _db
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.put(
            f"/api/v1/libraries/{lib_id}",
            json={"name": "NewName", "enabled": False},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["name"] == "NewName"
        assert data["enabled"] is False

    def test_delete_library(self, admin_client, app):
        from onani.models import ExternalLibrary
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="ToDelete", path="/tmp/del", owner_id=admin.id)
            from onani import db as _db
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.delete(f"/api/v1/libraries/{lib_id}")
        assert resp.status_code == 200

        resp2 = client.get(f"/api/v1/libraries/{lib_id}")
        assert resp2.status_code == 404

    def test_delete_cascades_files(self, admin_client, app):
        """Deleting a library also removes its ExternalLibraryFile rows."""
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        import datetime
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="CascadeLib", path="/tmp/cascade", owner_id=admin.id)
            _db.session.add(lib)
            _db.session.flush()
            now = datetime.datetime.utcnow()
            f = ExternalLibraryFile(
                library_id=lib.id,
                file_path="/tmp/cascade/a.jpg",
                status="PENDING",
                first_seen_at=now,
                last_seen_at=now,
            )
            _db.session.add(f)
            _db.session.commit()
            lib_id = lib.id
            file_id = f.id

            # Delete inside the same app context to avoid SQLite identity-map issues.
            resp = client.delete(f"/api/v1/libraries/{lib_id}")
            assert resp.status_code == 200

            _db.session.expire_all()
            assert ExternalLibraryFile.query.get(file_id) is None


class TestLibraryScan:
    """Triggering and polling scans."""

    def test_scan_requires_admin(self, logged_in_client, app):
        from onani.models import ExternalLibrary
        from onani import db as _db
        client, user = logged_in_client
        with app.app_context():
            lib = ExternalLibrary(name="ScanPerm", path="/tmp/sp", owner_id=None)
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.post(f"/api/v1/libraries/{lib_id}/scan")
        assert resp.status_code == 403

    def test_scan_disabled_library_rejected(self, admin_client, app):
        from onani.models import ExternalLibrary
        from onani import db as _db
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="DisabledLib", path="/tmp/dl", enabled=False, owner_id=admin.id)
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.post(f"/api/v1/libraries/{lib_id}/scan")
        assert resp.status_code == 400

    def test_scan_triggers_task(self, admin_client, app):
        """POST /scan returns 202 and a task_id."""
        from onani.models import ExternalLibrary
        from onani import db as _db
        from unittest.mock import patch
        client, admin = admin_client
        with tempfile.TemporaryDirectory() as tmpdir:
            with app.app_context():
                lib = ExternalLibrary(name="ScanTrigger", path=tmpdir, owner_id=admin.id)
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

            # Patch apply_async to avoid actually running the task in this test.
            with patch("onani.routes.api.v1.libraries.scan_library.apply_async") as mock_async:
                mock_async.return_value = None
                resp = client.post(f"/api/v1/libraries/{lib_id}/scan")

            assert resp.status_code == 202
            data = json.loads(resp.data)
            assert "task_id" in data

    def test_get_scan_status_idle(self, admin_client, app):
        from onani.models import ExternalLibrary
        from onani import db as _db
        client, admin = admin_client
        with app.app_context():
            lib = ExternalLibrary(name="IdleLib", path="/tmp/idle", owner_id=admin.id)
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

        resp = client.get(f"/api/v1/libraries/{lib_id}/scan")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["library_id"] == lib_id


class TestLibraryFileList:
    """Listing files tracked for a library."""

    def test_files_requires_moderator(self, client, app):
        resp = client.get("/api/v1/libraries/1/files")
        # Flask-Login redirects unauthenticated requests; flask-restful returns 403
        assert resp.status_code in (401, 403)

    def test_files_returns_paginated(self, admin_client, app):
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        client, admin = admin_client
        import datetime
        with app.app_context():
            lib = ExternalLibrary(name="FileListLib", path="/tmp/fl", owner_id=admin.id)
            _db.session.add(lib)
            _db.session.flush()
            now = datetime.datetime.utcnow()
            for i in range(5):
                _db.session.add(ExternalLibraryFile(
                    library_id=lib.id,
                    file_path=f"/tmp/fl/img{i}.jpg",
                    status="PENDING",
                    first_seen_at=now,
                    last_seen_at=now,
                ))
            _db.session.commit()
            lib_id = lib.id

        resp = client.get(f"/api/v1/libraries/{lib_id}/files?per_page=3")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total"] == 5
        assert len(data["data"]) == 3

    def test_files_filter_by_status(self, admin_client, app):
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        client, admin = admin_client
        import datetime
        with app.app_context():
            lib = ExternalLibrary(name="FilterLib", path="/tmp/flt", owner_id=admin.id)
            _db.session.add(lib)
            _db.session.flush()
            now = datetime.datetime.utcnow()
            _db.session.add(ExternalLibraryFile(
                library_id=lib.id, file_path="/tmp/flt/a.jpg",
                status="IMPORTED", first_seen_at=now, last_seen_at=now,
            ))
            _db.session.add(ExternalLibraryFile(
                library_id=lib.id, file_path="/tmp/flt/b.jpg",
                status="FAILED", first_seen_at=now, last_seen_at=now, error="oops",
            ))
            _db.session.commit()
            lib_id = lib.id

        resp = client.get(f"/api/v1/libraries/{lib_id}/files?status=IMPORTED")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total"] == 1
        assert data["data"][0]["status"] == "IMPORTED"


class TestScanTask:
    """Unit-level tests for the scan_library Celery task (runs eagerly)."""

    def test_scan_nonexistent_path(self, app, make_user):
        from onani.models import ExternalLibrary
        from onani import db as _db
        from onani.tasks.library import scan_library

        with app.app_context():
            user = make_user(username="scanuser1", password="testpassword")
            lib = ExternalLibrary(name="NoDir", path="/nonexistent_path_xyz", owner_id=user.id)
            _db.session.add(lib)
            _db.session.commit()
            lib_id = lib.id

            result = scan_library(lib_id)
            assert "error" in result

            lib = ExternalLibrary.query.get(lib_id)
            assert lib.last_scan_status == "FAILED"

    def test_scan_empty_directory(self, app, make_user):
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        from onani.tasks.library import scan_library

        with app.app_context():
            user = make_user(username="scanuser2", password="testpassword")
            with tempfile.TemporaryDirectory() as tmpdir:
                lib = ExternalLibrary(name="EmptyDir", path=tmpdir, owner_id=user.id, default_rating="g")
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

                result = scan_library(lib_id)

                assert result["imported"] == 0
                lib = ExternalLibrary.query.get(lib_id)
                assert lib.last_scan_status == "SUCCESS"
                assert ExternalLibraryFile.query.filter_by(library_id=lib_id).count() == 0

    def test_scan_imports_image(self, app, make_user):
        """Scan should import a valid PNG file and create a Post."""
        from onani.models import ExternalLibrary, ExternalLibraryFile, Post
        from onani import db as _db
        from onani.tasks.library import scan_library

        with app.app_context():
            user = make_user(username="scanuser3", password="testpassword")
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write a minimal valid 1×1 PNG so PIL can parse it.
                import struct, zlib
                def _png_1x1():
                    sig = b'\x89PNG\r\n\x1a\n'
                    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                    idat_raw = zlib.compress(b'\x00\xff\x00\x00')
                    idat_crc = zlib.crc32(b'IDAT' + idat_raw) & 0xffffffff
                    idat = struct.pack('>I', len(idat_raw)) + b'IDAT' + idat_raw + struct.pack('>I', idat_crc)
                    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                    return sig + ihdr + idat + iend

                img_path = os.path.join(tmpdir, "test.png")
                with open(img_path, "wb") as fh:
                    fh.write(_png_1x1())

                lib = ExternalLibrary(
                    name="ImageDir", path=tmpdir, owner_id=user.id,
                    default_rating="g", default_tags="meta:test",
                )
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

                result = scan_library(lib_id)

                assert result["imported"] == 1
                assert result["failed"] == 0
                filerec = ExternalLibraryFile.query.filter_by(library_id=lib_id).first()
                assert filerec is not None
                assert filerec.status == "IMPORTED"
                assert filerec.post_id is not None

                post = Post.query.get(filerec.post_id)
                assert post is not None
                assert post.is_external is True
                assert post.imported_from.startswith("/external/ImageDir/")
                assert tmpdir not in post.imported_from

                media_path = os.path.join(app.config["IMAGES_DIR"], post.filename[:2], post.filename)
                assert not os.path.exists(media_path)

    def test_external_route_serves_file_and_hides_when_disabled(self, app, make_user, client):
        from onani.models import ExternalLibrary
        from onani import db as _db
        from onani.tasks.library import scan_library
        import uuid

        with app.app_context():
            user = make_user(username="scanuser_external_route", password="testpassword")
            with tempfile.TemporaryDirectory() as tmpdir:
                import struct, zlib

                def _png_1x1():
                    sig = b'\x89PNG\r\n\x1a\n'
                    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                    idat_raw = zlib.compress(b'\x00\xff\xff\x00')
                    idat_crc = zlib.crc32(b'IDAT' + idat_raw) & 0xffffffff
                    idat = struct.pack('>I', len(idat_raw)) + b'IDAT' + idat_raw + struct.pack('>I', idat_crc)
                    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                    return sig + ihdr + idat + iend

                img_path = os.path.join(tmpdir, "a.png")
                with open(img_path, "wb") as fh:
                    fh.write(_png_1x1())

                lib_name = f"RouteLib-{uuid.uuid4().hex[:8]}"
                lib = ExternalLibrary(name=lib_name, path=tmpdir, owner_id=user.id)
                _db.session.add(lib)
                _db.session.commit()

                result = scan_library(lib.id)
                assert result["imported"] == 1

                ok = client.get(f"/external/{lib_name}/a.png")
                assert ok.status_code == 200

                lib = ExternalLibrary.query.get(lib.id)
                lib.enabled = False
                _db.session.commit()

                hidden = client.get(f"/external/{lib_name}/a.png")
                assert hidden.status_code == 404

    def test_scan_skips_duplicate_hash(self, app, make_user):
        """A second scan of the same directory should produce 0 new imports (all duplicates)."""
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        from onani.tasks.library import scan_library

        with app.app_context():
            user = make_user(username="scanuser4", password="testpassword")
            with tempfile.TemporaryDirectory() as tmpdir:
                import struct, zlib
                def _png_1x1():
                    sig = b'\x89PNG\r\n\x1a\n'
                    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                    idat_raw = zlib.compress(b'\x00\xff\x00\x00')
                    idat_crc = zlib.crc32(b'IDAT' + idat_raw) & 0xffffffff
                    idat = struct.pack('>I', len(idat_raw)) + b'IDAT' + idat_raw + struct.pack('>I', idat_crc)
                    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                    return sig + ihdr + idat + iend

                img_path = os.path.join(tmpdir, "dup.png")
                # Use a different pixel colour from the other tests to get a unique sha256.
                def _png_1x1_blue():
                    sig = b'\x89PNG\r\n\x1a\n'
                    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
                    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                    idat_raw = zlib.compress(b'\x00\x00\x00\xff')  # blue pixel
                    idat_crc = zlib.crc32(b'IDAT' + idat_raw) & 0xffffffff
                    idat = struct.pack('>I', len(idat_raw)) + b'IDAT' + idat_raw + struct.pack('>I', idat_crc)
                    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                    return sig + ihdr + idat + iend

                with open(img_path, "wb") as fh:
                    fh.write(_png_1x1_blue())

                lib = ExternalLibrary(
                    name="DupDir", path=tmpdir, owner_id=user.id, default_rating="g"
                )
                _db.session.add(lib)
                _db.session.commit()
                lib_id = lib.id

                # First scan — imports the file.
                r1 = scan_library(lib_id)
                assert r1["imported"] == 1, f"First scan should import 1 file, got {r1}"

                # Second scan — should produce 0 new imports (file already IMPORTED).
                r2 = scan_library(lib_id)
                assert r2["imported"] == 0
                assert r2["failed"] == 0

    def test_scan_marks_missing_files(self, app, make_user):
        """Files tracked from a previous scan that disappear on disk are marked MISSING."""
        from onani.models import ExternalLibrary, ExternalLibraryFile
        from onani import db as _db
        from onani.tasks.library import scan_library
        import datetime

        with app.app_context():
            user = make_user(username="scanuser5", password="testpassword")
            with tempfile.TemporaryDirectory() as tmpdir:
                lib = ExternalLibrary(name="MissingDir", path=tmpdir, owner_id=user.id, default_rating="g")
                _db.session.add(lib)
                _db.session.flush()
                now = datetime.datetime.utcnow()
                ghost = ExternalLibraryFile(
                    library_id=lib.id,
                    file_path="/nonexistent/ghost.jpg",
                    status="PENDING",
                    first_seen_at=now,
                    last_seen_at=now,
                )
                _db.session.add(ghost)
                _db.session.commit()
                lib_id = lib.id
                ghost_id = ghost.id

                scan_library(lib_id)

                ghost_fresh = ExternalLibraryFile.query.get(ghost_id)
                assert ghost_fresh.status == "MISSING"
