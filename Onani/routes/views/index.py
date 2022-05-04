# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 03:01:07
from flask import render_template, request, redirect, url_for
from Onani.models import Ban, Post, Tag

from . import main, db


@main.route("/")
def index():
    return redirect(url_for("main.post_index"))

    # # render the index template
    # return render_template(
    #     "/index.jinja2",
    #     tags=tags,
    #     posts=posts,
    # )
