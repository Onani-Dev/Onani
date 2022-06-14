# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-06-14 21:07:24

from flask import render_template

from . import main


@main.route("/erpcomponents")
def erptest():
    return render_template("/routes/roleplay/index.jinja2")
