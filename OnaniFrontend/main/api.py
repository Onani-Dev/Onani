# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 16:15:08
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-21 18:55:50
import hashlib
import os
from urllib.request import urlopen

from flask import abort, jsonify, request
from flask_login import current_user, login_required

from OnaniCore import *
from OnaniCore.utils import (
    is_legal_password,
    is_safe_email,
    is_safe_username,
)

from . import main_api


@main_api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    if request.json is None:
        abort(400)

    settings = dict()

    if request.json.get("username"):
        if not is_safe_username(request.json["username"]):
            raise OnaniApiError("Username has illegal characters.")
        current_user.edit_username(html_escape(request.json["username"]))

    if request.json.get("email"):
        if not is_safe_email(request.json["email"]):
            raise OnaniApiError("Invalid Email.")
        current_user.edit_email(html_escape(request.json["email"]))

    if request.json.get("new_password"):
        if request.json.get("new_password") != request.json.get("confirm_password"):
            raise OnaniApiError("Passwords did not match")

        if not is_legal_password(request.json.get("new_password")):
            raise OnaniApiError("Password has illegal characters")

        try:
            current_user.edit_password(
                request.json.get("current_password"), request.json.get("new_password")
            )
        except OnaniAuthenticationError:
            raise OnaniApiError("Incorrect Password.")

    if request.json.get("avatar"):
        try:
            with urlopen(request.json["avatar"]) as response:
                data = response.read()
        except ValueError:
            abort(400)

        if not os.path.isdir("./OnaniFrontend/static/data/avatars/"):
            os.makedirs("./OnaniFrontend/static/data/avatars/")
        avatar_filename = f"./OnaniFrontend/static/data/avatars/{hashlib.md5(str(current_user.id).encode()).hexdigest()}.png"

        with open(avatar_filename, "wb") as f:
            f.write(data)

        settings["profile_pic"] = avatar_filename.replace("./OnaniFrontend/static", "")

    if request.json.get("bio"):
        if request.json["bio"] != current_user.settings.bio:
            settings["bio"] = html_escape(request.json["bio"])

    if len(settings) > 0:
        current_user.edit_settings(**settings)

    return (
        jsonify({"ok": True}),
        200,
    )
