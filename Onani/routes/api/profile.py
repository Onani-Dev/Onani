# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:45:07
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 02:46:53
import json

from flask import flash, jsonify, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from . import admin_api, db, main_api


@main_api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    pass
