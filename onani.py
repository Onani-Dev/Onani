# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-07 17:44:35

import logging
import os
import random
from datetime import timedelta

import pymongo
from flask import Flask, abort, redirect, render_template, request, send_from_directory
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sockets import Sockets

from OnaniCore import *

app = Flask(
    __name__,
    static_url_path="",
    static_folder="OnaniFrontend/static",
    template_folder="OnaniFrontend/views",
)
# Temporary secret key; Change to config generated one
app.config["SECRET_KEY"] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"
login_manager = LoginManager()
onaniDB = DatabaseController("mongodb://localhost:27017/")
login_manager.init_app(app)
sockets = Sockets(app)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@login_manager.user_loader
def user_loader(username):
    user = onaniDB.get_user(username=username)
    if user is None:
        return
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template(
            "/index.html", tags=onaniDB.get_tags(limit=25, sort="post_count")
        )
    else:
        user = onaniDB.get_user(username=request.form["username"])
        if user is None:
            return redirect("/login")
        if user.authenticate(request.form["password"]):
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                return redirect("/")

        return redirect("/login")


@app.route("/")
@app.route("/posts")
def index():
    tags = onaniDB.get_tags(limit=25, sort="post_count")
    # for tag in tags:
    #     tag.edit_type(TagType(random.randint(0, 5)))
    return render_template("/index.html", tags=tags)


@app.route("/profile")
@login_required
def profile():
    return current_user.username


if __name__ == "__main__":
    app.run()
