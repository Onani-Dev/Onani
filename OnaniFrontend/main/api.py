# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 16:15:08
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-16 00:58:55
import time
import os
import uuid
from urllib.request import urlopen
from flask import abort, redirect, request, jsonify
from flask_login import current_user, login_required
from OnaniCore import *
from . import main_api


@main_api.route("/test", methods=["GET"])
@login_required
def test():
    return current_user.username + " " + current_user.api_key


@main_api.route("/longrun", methods=["GET"])
def longrun():
    for x in range(30):
        time.sleep(1)
    return "Slept for 30 seconds."


@main_api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    if request.json is None:
        abort(400)
    try:
        request.json["bio"]
        request.json["avatar"]
    except KeyError:
        abort(400)

    settings = dict()

    if request.json["avatar"] is not None:
        try:
            with urlopen(request.json["avatar"]) as response:
                data = response.read()
        except ValueError:
            abort(400)
        if not os.path.isdir("./OnaniFrontend/static/user_data/avatars/"):
            os.makedirs("./OnaniFrontend/static/user_data/avatars/")
        avatar_filename = (
            f"./OnaniFrontend/static/user_data/avatars/{str(uuid.uuid4())}.png"
        )
        with open(avatar_filename, "wb") as f:
            f.write(data)
        settings["profile_pic"] = avatar_filename.replace("./OnaniFrontend/static", "")

    if request.json["bio"] != current_user.settings.bio:
        settings["bio"] = html_escape(request.json["bio"])

    current_user.edit_settings(**settings)

    return (
        jsonify({"ok": True}),
        200,
    )

