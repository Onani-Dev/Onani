# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-05 00:53:29

from flask import render_template

from . import main


@main.route("/generate_204")
def gen_204():
    return "", 204


@main.route("/dmca/")
def dmca_page():
    return render_template("/dmca.jinja2")
