# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-10 22:13:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 01:29:04
from flask import render_template

from Onani.models import Tag, User, UserSettings

from . import main


@main.route("/upload/")
def upload():
    # Get the tags sorted by the post count
    return render_template("/upload.jinja2")
