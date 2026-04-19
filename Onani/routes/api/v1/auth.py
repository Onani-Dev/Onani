# -*- coding: utf-8 -*-
"""Authentication API endpoints for the Vue SPA.

All endpoints return JSON. Login/register set a Flask-Login session cookie.
The CSRF token endpoint lets the SPA bootstrap the X-CSRFToken header.
"""
import html
from datetime import timedelta

from flask import make_response, request, session
from flask_login import current_user, login_required, login_user, logout_user
from flask_restful import Resource, reqparse
from flask_wtf.csrf import generate_csrf
from Onani.models import User, UserSchema
from Onani.services.auth import (
    AuthError,
    BannedError,
    DeletedAccountError,
    InvalidCredentialsError,
    verify_credentials,
)
from Onani.services import create_user

from . import api, db, limiter


class AuthLogin(Resource):
    decorators = [limiter.limit("10/minute")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("username", location="json", type=str, required=True, trim=True)
        parser.add_argument("password", location="json", type=str, required=True)
        parser.add_argument("otp", location="json", type=int, required=False, default=None)
        args = parser.parse_args()

        user = User.query.filter_by(username=html.escape(args["username"])).first()
        if not user:
            return {"message": "Invalid username or password."}, 401

        try:
            verify_credentials(user, args["password"], args["otp"])
        except InvalidCredentialsError as e:
            return {"message": str(e)}, 401
        except BannedError as e:
            return {"message": str(e)}, 403
        except DeletedAccountError as e:
            return {"message": str(e)}, 403

        login_user(user, remember=True, duration=timedelta(days=7))

        # Cache password for encrypted cookies decryption in imports
        if user.settings and user.settings.encrypted_cookies:
            session["_cookie_pw"] = args["password"]

        resp = make_response(UserSchema().dump(current_user), 200)
        resp.set_cookie(
            "current_user_id",
            str(current_user.id),
            samesite="Lax",
            secure=request.is_secure,
            httponly=False,  # intentionally readable by JS for UX
        )
        return resp


class AuthLogout(Resource):
    decorators = [login_required]

    def post(self):
        logout_user()
        resp = make_response({"message": "Successfully logged out."}, 200)
        resp.delete_cookie("current_user_id")
        return resp


class AuthRegister(Resource):
    decorators = [limiter.limit("10/hour")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("username", location="json", type=str, required=True, trim=True)
        parser.add_argument("password", location="json", type=str, required=True)
        parser.add_argument("email", location="json", type=str, required=False, default=None, trim=True)
        args = parser.parse_args()

        # Validate username uniqueness
        if User.query.filter_by(username=html.escape(args["username"])).first():
            return {"message": "Username is already taken."}, 409

        if len(args["password"]) < 8:
            return {"message": "Password must be at least 8 characters."}, 400

        try:
            user = create_user(
                username=args["username"],
                password=args["password"],
                email=args["email"] or None,
            )
        except ValueError as e:
            return {"message": str(e)}, 400

        login_user(user, remember=True, duration=timedelta(days=7))

        resp = make_response(UserSchema().dump(current_user), 201)
        resp.set_cookie(
            "current_user_id",
            str(current_user.id),
            samesite="Strict",
            secure=True,
            httponly=False,
        )
        return resp


class AuthMe(Resource):
    def get(self):
        if not current_user.is_authenticated:
            return {"authenticated": False}, 401
        return {"authenticated": True, **UserSchema().dump(current_user)}


class AuthCsrf(Resource):
    """Return a fresh CSRF token for the SPA to use in X-CSRFToken headers."""

    def get(self):
        return {"csrf_token": generate_csrf()}


api.add_resource(AuthLogin, "/auth/login")
api.add_resource(AuthLogout, "/auth/logout")
api.add_resource(AuthRegister, "/auth/register")
api.add_resource(AuthMe, "/auth/me")
api.add_resource(AuthCsrf, "/auth/csrf")
