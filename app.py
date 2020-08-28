# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-28 21:26:36

import logging
import os

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

onaniDB = DatabaseController("mongodb://localhost:27017/")
sockets = Sockets(app)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@app.route("/")
@app.route("/posts")
def index():
    return render_template("/index.html", tags=onaniDB.get_tags(limit=25))


if __name__ == "__main__":
    app.run()
