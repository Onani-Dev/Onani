# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-18 21:15:48
from flask import render_template, request, redirect
from Onani.models import Ban, Post, Tag

from . import main, db


@main.route("/")
def posts():
    return redirect("/posts/")

    # # render the index template
    # return render_template(
    #     "/index.jinja2",
    #     tags=tags,
    #     posts=posts,
    # )
