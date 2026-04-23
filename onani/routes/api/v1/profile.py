# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-10 12:45:23
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-04 16:03:50

from flask import current_app, request, session
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from onani.controllers.crypto import encrypt_cookies, decrypt_cookies
from onani.services.files import create_avatar
from onani.models import UserSchema, User

from . import api, db, limiter


class Profile(Resource):
    decorators = [login_required]

    @staticmethod
    def _payload(user):
        """Return profile payload for the current user, including private email."""
        data = UserSchema().dump(user)
        data["email"] = user.email
        return data

    def get(self):
        return self._payload(current_user)

    def put(self):
        parser = reqparse.RequestParser()

        # ACCOUNT SETTINGS
        parser.add_argument(
            "nickname", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "email", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "new_password", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "current_password", location="json", type=str, default=None, required=False
        )
        # TODO: figure out a good way to not have to resort to default=False
        parser.add_argument(
            "otp_enabled", location="json", type=bool, default=None, required=False
        )

        # PROFILE SETTINGS
        parser.add_argument(
            "biography", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "profile_picture", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "remove_profile_picture", location="json", type=bool, default=False, required=False
        )
        parser.add_argument(
            "profile_colour", location="json", type=str, default=None, required=False
        )
        parser.add_argument(
            "sfw_mode", location="json", type=bool, default=None, required=False
        )

        # Parse the args
        args = parser.parse_args()

        # ACCOUNT SETTINGS
        if args["nickname"] is not None:
            current_user.nickname = args["nickname"] or None

        if args["email"]:
            if not current_user.check_password(args["current_password"] or ""):
                from flask import abort
                abort(403, description="Current password is required to change your email.")
            current_user.email = args["email"]

        if args["new_password"] and current_user.check_password(
            args["current_password"]
        ):
            if len(args["new_password"]) < 8:
                return {"message": "Password must be at least 8 characters."}, 400
            current_user.set_password(args["new_password"])

        if args["otp_enabled"] is not None:
            if not args["otp_enabled"] and current_user.otp_enabled:
                if not current_user.check_password(args.get("current_password") or ""):
                    return {"message": "Current password is required to disable 2FA."}, 403
            current_user.otp_enabled = args["otp_enabled"]

        # PROFILE SETTINGS
        if args["biography"]:
            current_user.settings.biography = args["biography"]

        if args["profile_colour"]:
            current_user.settings.profile_colour = args["profile_colour"]

        if args["sfw_mode"] is not None:
            current_user.settings.sfw_mode = args["sfw_mode"]

        if args["profile_picture"]:
            try:
                create_avatar(current_user, args["profile_picture"],
                              avatars_dir=current_app.config.get("AVATARS_DIR", "/avatars"))
            except Exception as e:
                return {"message": f"Avatar upload failed: {e}"}, 400

        if args["remove_profile_picture"]:
            import os

            avatars_dir = current_app.config.get("AVATARS_DIR", "/avatars")
            if current_user.settings.avatar:
                old_path = os.path.join(avatars_dir, os.path.basename(current_user.settings.avatar))
                if os.path.exists(old_path):
                    os.remove(old_path)
            current_user.settings.avatar = None

        db.session.commit()

        return self._payload(current_user)

    def patch(self):
        return self.put()


class ProfileCookies(Resource):
    """Upload or delete an encrypted gallery-dl cookies file."""
    decorators = [login_required]

    def get(self):
        has = current_user.settings.encrypted_cookies is not None
        return {"has_cookies": has}

    def post(self):
        password = request.form.get("password")
        if not password or not current_user.check_password(password):
            return {"message": "Current password is required."}, 403

        file = request.files.get("cookies")
        if not file:
            return {"message": "No cookies file provided."}, 400

        data = file.read()
        if len(data) > 512 * 1024:
            return {"message": "Cookies file too large (max 512 KB)."}, 400

        token, salt = encrypt_cookies(data, password)
        current_user.settings.encrypted_cookies = token
        current_user.settings.cookies_salt = salt
        db.session.commit()

        # Cache the password in server-side session so imports can decrypt
        session["_cookie_pw"] = password

        return {"message": "Cookies saved."}

    def delete(self):
        current_user.settings.encrypted_cookies = None
        current_user.settings.cookies_salt = None
        db.session.commit()
        session.pop("_cookie_pw", None)
        return {"message": "Cookies removed."}


class ProfileOTP(Resource):
    """TOTP 2FA setup, verification, and disable."""
    decorators = [login_required]

    def get(self):
        """Return current OTP status and QR code for setup."""
        import io, base64
        import qrcode

        uri = current_user.otp_uri
        buf = io.BytesIO()
        qrcode.make(uri).save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        return {
            "enabled": current_user.otp_enabled,
            "uri": uri,
            "qr_code": f"data:image/png;base64,{qr_b64}",
            "secret": current_user.otp_token,
        }

    def post(self):
        """Verify a TOTP code and enable 2FA."""
        parser = reqparse.RequestParser()
        parser.add_argument("code", location="json", type=int, required=True)
        args = parser.parse_args()

        if not current_user.check_otp(args["code"]):
            return {"message": "Invalid OTP code."}, 400

        current_user.otp_enabled = True
        db.session.commit()
        return {"enabled": True}

    def delete(self):
        """Disable 2FA."""
        parser = reqparse.RequestParser()
        parser.add_argument("password", location="json", type=str, required=True)
        args = parser.parse_args()

        if not current_user.check_password(args["password"]):
            return {"message": "Incorrect password."}, 403

        current_user.otp_enabled = False
        db.session.commit()
        return {"enabled": False}


api.add_resource(Profile, "/profile")
api.add_resource(ProfileCookies, "/profile/cookies")
api.add_resource(ProfileOTP, "/profile/otp")
