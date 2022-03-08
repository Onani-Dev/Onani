# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 03:01:15

from flask import render_template

from . import main


@main.route("/fun")
def sonic_fun():
    return render_template("/fun.jinja2")
