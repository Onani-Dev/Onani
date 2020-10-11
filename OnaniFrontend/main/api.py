# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 16:15:08
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-12 01:41:46
from OnaniCore.models.commentary import Commentary
import hashlib
import os
from datetime import datetime
from urllib.request import urlopen

from flask import abort, jsonify, request
from flask_login import current_user, login_required
from OnaniCore import *
from OnaniCore import __version__
from OnaniCore.utils import (
    is_legal_password,
    is_safe_email,
    is_safe_username,
    make_api_response,
    parse_tags,
)
from werkzeug.datastructures import FileStorage

from . import main, main_api, onaniDB


@main_api.route("/", methods=["GET"])
def api_index():
    return make_api_response({"version": __version__})


@main_api.route("/users/<user_id>", methods=["GET"])
@login_required
def view_profile(user_id):
    if not user_id.isdigit():
        raise OnaniApiError("Invalid User ID.")

    user_id = int(user_id)

    try:
        user = onaniDB.get_user(id=user_id)
    except OnaniDatabaseException:
        raise OnaniApiError("User was not found.", 404)

    return make_api_response(
        {
            "id": user.id,
            "username": user.username,
            "created_at": datetime.timestamp(user.created_at),
            "permissions": user.permissions.value,
            "profile": {
                "avatar": user.settings.avatar.to_dict(),
                "bio": user.settings.bio,
                "platforms": user.settings.platforms.to_dict(),
            },
        }
    )


@main_api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    if request.json is None:
        abort(400)

    settings = dict()

    if request.json.get("username"):
        if not is_safe_username(request.json["username"]):
            raise OnaniApiError("Username has illegal characters.")
        current_user.username = html_escape(request.json["username"])

    if request.json.get("email"):
        if not is_safe_email(request.json["email"]):
            raise OnaniApiError("Invalid Email.")
        current_user.email = html_escape(request.json["email"])

    if request.json.get("new_password"):
        if request.json.get("new_password") != request.json.get("confirm_password"):
            raise OnaniApiError("Passwords did not match")

        if not is_legal_password(request.json.get("new_password")):
            raise OnaniApiError("Password has illegal characters")

        try:
            current_user.change_password(
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

        try:
            avatar_file = onaniDB.file_controller.save_avatar(data)
        except ValueError:
            raise OnaniApiError("Image was not square, Width and height did not match.")

        settings["avatar"] = avatar_file

    if request.json.get("bio") or request.json.get("bio") == "":
        if request.json["bio"] != current_user.settings.bio:
            settings["bio"] = html_escape(request.json["bio"])

    if request.json.get("platforms"):
        platforms = request.json["platforms"]
        for p in list(platforms):
            platforms[p] = html_escape(platforms[p])
        current_user.edit_platforms(**platforms)

    if request.json.get("custom_css") or request.json.get("custom_css") == "":
        if request.json["custom_css"] != current_user.settings.custom_css:
            settings["custom_css"] = html_escape(request.json["custom_css"])

    if request.json.get("tag_blacklist") or request.json.get("tag_blacklist") == []:
        if not isinstance(request.json.get("tag_blacklist"), list):
            abort(400)
        if request.json["tag_blacklist"] != current_user.settings.tag_blacklist:
            settings["tag_blacklist"] = parse_tags(
                [html_escape(x) for x in request.json["tag_blacklist"]]
            )

    if len(settings) > 0:
        current_user.edit_settings(**settings)

    return make_api_response()


@main_api.route("/upload", methods=["POST"])
@login_required
def upload():
    uploaded_file: FileStorage = request.files["file"]
    if uploaded_file.filename != "":
        filetype = uploaded_file.mimetype.split("/")[1]
        if filetype in ["jpeg", "jpg", "gif", "png", "webp", "jfif"]:
            post_file = onaniDB.file_controller.save_file(
                uploaded_file.read(), filetype
            )
            post = onaniDB.add_post(
                post_file=post_file,
                source=request.form.get("source", ""),
                uploader=current_user,
                commentary=Commentary(onaniDB),
                tags=list(),  # TODO
            )
            return make_api_response({"path": f"/post/{post.id}"})
        raise OnaniApiError("Invalid File Type.")
    raise OnaniApiError("File not given.")
