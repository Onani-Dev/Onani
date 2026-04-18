# -*- coding: utf-8 -*-
"""Tests for UserSettings model validation."""
import pytest


class TestUserSettingsModel:
    def test_biography_max_length(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="biouser")
            with pytest.raises(ValueError, match="too large"):
                user.settings.biography = "x" * 5121

    def test_biography_html_escaped(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="bioescape")
            user.settings.biography = "<b>Bold</b>"
            db.session.commit()
            assert "<b>" not in user.settings.biography
            assert "&lt;" in user.settings.biography

    def test_biography_none_ok(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="bionone")
            user.settings.biography = None
            db.session.commit()
            assert user.settings.biography is None

    def test_connections_invalid_github_url(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="badgithub")
            with pytest.raises(ValueError, match="github connection did not match"):
                user.settings.connections = {
                    "deviantart": None,
                    "discord": None,
                    "github": "not-a-github-url",
                    "patreon": None,
                    "paypal": None,
                    "pixiv": None,
                    "twitter": None,
                }

    def test_connections_valid_github_url(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="goodgithub")
            user.settings.connections = {
                "deviantart": None,
                "discord": None,
                "github": "https://github.com/testuser",
                "patreon": None,
                "paypal": None,
                "pixiv": None,
                "twitter": None,
            }
            db.session.commit()
            assert "github.com/testuser" in user.settings.connections["github"]

    def test_connections_too_long(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="toolongconn")
            with pytest.raises(ValueError, match="too long"):
                user.settings.connections = {
                    "deviantart": None,
                    "discord": "x" * 65,
                    "github": None,
                    "patreon": None,
                    "paypal": None,
                    "pixiv": None,
                    "twitter": None,
                }

    def test_connections_none_values_ok(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="allnoneconn")
            user.settings.connections = {
                "deviantart": None,
                "discord": None,
                "github": None,
                "patreon": None,
                "paypal": None,
                "pixiv": None,
                "twitter": None,
            }
            db.session.commit()
            assert user.settings.connections["github"] is None

    def test_sfw_mode_defaults_to_false(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="sfwdefault")
            assert user.settings.sfw_mode is False

    def test_sfw_mode_can_be_enabled(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="sfwenable")
            user.settings.sfw_mode = True
            db.session.commit()
            db.session.refresh(user.settings)
            assert user.settings.sfw_mode is True

    def test_sfw_mode_can_be_toggled_back(self, app, db, make_user):
        with app.app_context():
            user = make_user(username="sfwtoggle")
            user.settings.sfw_mode = True
            db.session.commit()
            user.settings.sfw_mode = False
            db.session.commit()
            db.session.refresh(user.settings)
            assert user.settings.sfw_mode is False
