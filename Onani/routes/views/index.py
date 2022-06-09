# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:59:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-09 04:47:03
from flask import render_template, request, redirect, url_for, abort, current_app
from Onani.models import Ban, Post, Tag

from . import main, db


@main.route("/")
def index():
    latest = Post.query.order_by(Post.id.desc()).limit(7)

    first_post = latest.first()

    return render_template("/index.jinja2", latest=latest, first_post=first_post)
