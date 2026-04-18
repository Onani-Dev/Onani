# -*- coding: utf-8 -*-
"""Tests for the JSON auth API endpoints (/api/v1/auth/*)."""
import pytest


class TestLoginAPI:
    def test_login_wrong_password(self, client, make_user, app):
        with app.app_context():
            make_user(username="loginuser", password="correctpass")

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "loginuser", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_user_not_found(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "doesnotexist", "password": "irrelevant"},
        )
        assert resp.status_code == 401

    def test_login_success(self, client, make_user, app):
        with app.app_context():
            make_user(username="successlogin", password="mypassword")

        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "successlogin", "password": "mypassword"},
        )
        assert resp.status_code == 200
        assert resp.json["username"] == "successlogin"


class TestRegisterAPI:
    def test_register_success(self, client, app):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newreguser",
                "password": "Password123",
            },
        )
        assert resp.status_code == 201
        assert resp.json["username"] == "newreguser"

    def test_register_duplicate_username(self, client, make_user, app):
        with app.app_context():
            make_user(username="existinguser")
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "existinguser", "password": "Password123"},
        )
        assert resp.status_code == 409

    def test_register_missing_fields(self, client):
        resp = client.post("/api/v1/auth/register", json={"username": "nopass"})
        assert resp.status_code == 400


class TestLogoutAPI:
    def test_logout_requires_login(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401

    def test_logout_success(self, logged_in_client):
        client, user = logged_in_client
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 200


class TestAuthMeAPI:
    def test_me_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json["authenticated"] is False

    def test_me_authenticated(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json["authenticated"] is True


class TestAuthCsrfAPI:
    def test_csrf_returns_token(self, client):
        resp = client.get("/api/v1/auth/csrf")
        assert resp.status_code == 200
        assert "csrf_token" in resp.json

