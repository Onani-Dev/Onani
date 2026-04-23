# -*- coding: utf-8 -*-
"""Tests for the utils module."""
import pytest
from unittest.mock import Mock


class TestUtils:
    def test_is_url_valid(self):
        from onani.controllers.utils import is_url
        assert is_url("https://example.com") is True
        assert is_url("http://www.example.com/path?q=1") is True

    def test_is_url_invalid(self):
        from onani.controllers.utils import is_url
        assert is_url("not-a-url") is False
        assert is_url("ftp://example.com") is False

    def test_url_hostname(self):
        from onani.controllers.utils import url_hostname
        assert url_hostname("https://example.com/path") == "example.com"

    def test_url_hostname_non_url(self):
        from onani.controllers.utils import url_hostname
        result = url_hostname("just-a-string")
        assert result == "just-a-string" or result is None

    def test_hex_to_rgb(self):
        from onani.controllers.utils import hex_to_rgb
        r, g, b = hex_to_rgb("#ff0000")
        assert r == 255
        assert g == 0
        assert b == 0

    def test_rgb_to_hex(self):
        from onani.controllers.utils import rgb_to_hex
        assert rgb_to_hex((255, 0, 0)) == "#ff0000"
        assert rgb_to_hex((0, 255, 0)) == "#00ff00"

    def test_colour_contrast_light_bg(self):
        from onani.controllers.utils import colour_contrast
        # Light background -> dark text
        assert colour_contrast("#ffffff") == "#000000"

    def test_colour_contrast_dark_bg(self):
        from onani.controllers.utils import colour_contrast
        # Dark background -> light text
        assert colour_contrast("#000000") == "#ffffff"

    def test_natural_join_empty(self):
        from onani.controllers.utils import natural_join
        assert natural_join([]) == ""

    def test_natural_join_single(self):
        from onani.controllers.utils import natural_join
        assert natural_join(["one"]) == "one"

    def test_natural_join_two(self):
        from onani.controllers.utils import natural_join
        assert natural_join(["one", "two"]) == "one and two"

    def test_natural_join_three(self):
        from onani.controllers.utils import natural_join
        result = natural_join(["one", "two", "three"])
        assert "one" in result
        assert "and three" in result

    def test_natural_join_truncate(self):
        from onani.controllers.utils import natural_join
        result = natural_join(["a", "b", "c", "d", "e"], max_length=3)
        assert "2 more" in result

    def test_startswith_min_passes(self):
        from onani.controllers.utils import startswith_min
        assert startswith_min("artist:foo", "art", min_len=3) is True

    def test_startswith_min_min_len_not_met(self):
        from onani.controllers.utils import startswith_min
        # Start string "ar" (len 2) is less than min_len 3 -> False
        assert startswith_min("artist:foo", "ar", min_len=3) is False


class TestMaintenanceSqlSanitizer:
    def test_sanitize_postgres_restore_sql_removes_transaction_timeout(self):
        from onani.services.maintenance import _sanitize_postgres_restore_sql

        raw = (
            b"SET statement_timeout = 0;\n"
            b"SET transaction_timeout = 0;\n"
            b"SET lock_timeout = 0;\n"
            b"CREATE TABLE example(id integer);\n"
        )

        sanitized = _sanitize_postgres_restore_sql(raw).decode("utf-8")

        assert "SET transaction_timeout = 0;" not in sanitized
        assert "SET statement_timeout = 0;" in sanitized
        assert "SET lock_timeout = 0;" in sanitized
        assert "CREATE TABLE example" in sanitized

    def test_sanitize_postgres_restore_sql_is_noop_without_unsupported_settings(self):
        from onani.services.maintenance import _sanitize_postgres_restore_sql

        raw = b"SET statement_timeout = 0;\nSELECT 1;\n"
        sanitized = _sanitize_postgres_restore_sql(raw)

        assert sanitized == raw

    def test_restore_postgres_backup_retries_on_deadlock(self, monkeypatch):
        from onani.services import maintenance

        monkeypatch.setattr(maintenance, "_try_terminate_postgres_connections", lambda _db: None)
        monkeypatch.setattr(maintenance.time, "sleep", lambda _seconds: None)

        fake_engine = Mock()
        fake_engine.url.database = "onani_db"
        fake_db = Mock()
        fake_db.engine = fake_engine
        monkeypatch.setattr(maintenance, "db", fake_db)

        fake_cmd = ["psql"]
        fake_env = {"PGPASSWORD": "x"}
        monkeypatch.setattr(maintenance, "_postgres_cli_base", lambda _program: (fake_cmd, fake_env))

        calls = {"n": 0}

        class Proc:
            def __init__(self, returncode, stderr):
                self.returncode = returncode
                self.stderr = stderr

        def fake_run(*_args, **_kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return Proc(1, b"ERROR: deadlock detected")
            return Proc(0, b"")

        monkeypatch.setattr(maintenance.subprocess, "run", fake_run)

        result = maintenance._restore_postgres_backup(b"SELECT 1;")
        assert result == "PostgreSQL database restored from backup."
        assert calls["n"] == 2

    def test_restore_postgres_backup_raises_after_deadlock_retries(self, monkeypatch):
        from onani.services import maintenance

        monkeypatch.setattr(maintenance, "_try_terminate_postgres_connections", lambda _db: None)
        monkeypatch.setattr(maintenance.time, "sleep", lambda _seconds: None)

        fake_engine = Mock()
        fake_engine.url.database = "onani_db"
        fake_db = Mock()
        fake_db.engine = fake_engine
        monkeypatch.setattr(maintenance, "db", fake_db)

        fake_cmd = ["psql"]
        fake_env = {"PGPASSWORD": "x"}
        monkeypatch.setattr(maintenance, "_postgres_cli_base", lambda _program: (fake_cmd, fake_env))

        class Proc:
            def __init__(self, returncode, stderr):
                self.returncode = returncode
                self.stderr = stderr

        monkeypatch.setattr(
            maintenance.subprocess,
            "run",
            lambda *_args, **_kwargs: Proc(1, b"ERROR: deadlock detected"),
        )

        with pytest.raises(maintenance.MaintenanceError, match="deadlock detected"):
            maintenance._restore_postgres_backup(b"SELECT 1;")
