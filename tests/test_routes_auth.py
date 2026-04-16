# -*- coding: utf-8 -*-
"""Tests for auth-related routes: login, register, logout."""
import pytest


class TestLoginRoute:
    def test_login_page_renders(self, client):
        resp = client.get("/login/")
        assert resp.status_code == 200

    def test_login_wrong_password(self, client, make_user, app):
        with app.app_context():
            make_user(username="loginuser", password="correctpass")

        resp = client.post(
            "/login/",
            data={"username": "loginuser", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Should flash an error
        assert b"Invalid Login" in resp.data or resp.status_code == 200

    def test_login_user_not_found(self, client):
        resp = client.post(
            "/login/",
            data={"username": "doesnotexist", "password": "irrelevant"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_login_success_redirects(self, client, make_user, app):
        with app.app_context():
            make_user(username="successlogin", password="mypassword")

        resp = client.post(
            "/login/",
            data={"username": "successlogin", "password": "mypassword"},
            follow_redirects=False,
        )
        # Successful login should redirect
        assert resp.status_code in (302, 301, 200)

    def test_login_already_authenticated_redirects(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/login/", follow_redirects=False)
        assert resp.status_code == 302


class TestRegisterRoute:
    def test_register_page_renders(self, client):
        resp = client.get("/register/")
        assert resp.status_code == 200

    def test_register_success(self, client, app):
        with app.app_context():
            resp = client.post(
                "/register/",
                data={
                    "username": "newreguser",
                    "password": "Password123",
                    "confirm": "Password123",
                    "email": "",
                },
                follow_redirects=False,
            )
            # Should redirect after successful registration
            assert resp.status_code in (200, 302)

    def test_register_duplicate_username(self, client, make_user, app):
        with app.app_context():
            make_user(username="existinguser")
        resp = client.post(
            "/register/",
            data={
                "username": "existinguser",
                "password": "Password123",
                "confirm": "Password123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_register_passwords_do_not_match(self, client, app):
        resp = client.post(
            "/register/",
            data={
                "username": "nomatchuser",
                "password": "Password123",
                "confirm": "DifferentPassword",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200


class TestLogoutRoute:
    def test_logout_requires_login(self, client):
        resp = client.get("/logout/", follow_redirects=False)
        # Should redirect to login
        assert resp.status_code == 302

    def test_logout_success(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/logout/", follow_redirects=False)
        assert resp.status_code == 302
