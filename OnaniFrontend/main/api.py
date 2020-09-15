# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 16:15:08
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-15 17:42:51
import time

from flask import abort, redirect, request, jsonify
from flask_login import current_user, login_required

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
