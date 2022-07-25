# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-25 15:43:59
from flask import render_template
from Onani.controllers.database import query_posts
from Onani.models import Post

from . import db, main


@main.route("/")
def index():
    latest = query_posts().limit(7)

    first_post = latest.first()

    return render_template("/index.jinja2", latest=latest, first_post=first_post)
