# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-19 00:14:49
from flask import render_template, request, redirect
from Onani.models import Ban, Post, Tag

from . import main, db


@main.route("/")
# @main.route("/posts/")
def posts():
    return redirect("/posts/")





    # # render the index template
    # return render_template(
    #     "/index.jinja2",
    #     tags=tags,
    #     posts=posts,
    # )
