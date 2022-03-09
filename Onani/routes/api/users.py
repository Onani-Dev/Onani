# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:26:01
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 22:32:06
import json

from flask import abort, flash, jsonify, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from . import admin_api, db, main_api


@main_api.route("/users/<user_id>", methods=["GET"])
@login_required
def view_profile(user_id):
    if not user_id.isdigit():
        abort(404)

    user_id = int(user_id)
