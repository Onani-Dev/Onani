# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-06-14 00:24:51

from flask import render_template
from flask_login import login_required

from . import main


@main.route("/generate_204")
def gen_204():
    return "", 204


@main.route("/dmca/")
def dmca_page():
    return render_template("/routes/legal/dmca.jinja2")


@main.route("/terms/")
def terms_page():
    return render_template("/routes/legal/terms.jinja2")


@main.route("/privacy/")
def privacy_page():
    return render_template("/routes/legal/privacy.jinja2")


@main.route("/developers/")
@login_required
def devs_page():
    return render_template("/routes/developers/index.jinja2")
