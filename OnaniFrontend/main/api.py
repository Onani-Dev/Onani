# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 16:15:08
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 22:16:13
import hashlib
import os
import time
import uuid
from urllib.request import urlopen

import pybase64
from flask import abort, jsonify, redirect, request
from flask_login import current_user, login_required

from OnaniCore import *
from OnaniCore.utils import (
    check_if_safe_email,
    check_is_safe_username,
    check_if_legal_password,
)
from . import main_api


@main_api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    if request.json is None:
        abort(400)

    settings = dict()
    print(request.json)
    if request.json.get("username"):
        if not check_is_safe_username(request.json["username"]):
            raise OnaniApiError("Username has illegal characters.")
        current_user.edit_username(html_escape(request.json["username"]))

    if request.json.get("email"):
        if not check_if_safe_email(request.json["email"]):
            raise OnaniApiError("Invalid Email.")
        current_user.edit_email(html_escape(request.json["email"]))

    if request.json.get("new_password"):
        if request.json.get("new_password") != request.json.get("confirm_password"):
            raise OnaniApiError("Passwords did not match")

        if not check_if_legal_password(request.json.get("new_password")):
            raise OnaniApiError("Password had illegal characters")

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

    current_user.edit_settings(**settings)

    return (
        jsonify({"ok": True}),
        200,
    )
