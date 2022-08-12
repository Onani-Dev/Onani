# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-10 11:24:54
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 11:55:07

from flask import render_template
from flask_login import login_required
from Onani.controllers import permissions_required
from Onani.models import UserPermissions

from . import db, main


@main.route("/importer/", methods=["GET"])
@login_required
@permissions_required(UserPermissions.IMPORT_POSTS)
def importer():
    return render_template("base.jinja2")
