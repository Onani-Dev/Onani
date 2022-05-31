# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:57:52

from flask import render_template
from flask_login import login_required

from . import main


@main.route("/generate_204")
def gen_204():
    return "", 204


@main.route("/dmca/")
def dmca_page():
    return render_template("/routes/dmca/index.jinja2")


@main.route("/developers/")
@login_required
def devs_page():
    return render_template("/routes/developers/index.jinja2")
