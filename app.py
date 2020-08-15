# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-15 18:31:43

import logging
import os

import pymongo
from flask import Flask, render_template, send_from_directory
from flask_sockets import Sockets
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from OnaniCore import *

app = Flask(
    __name__,
    static_url_path="",
    static_folder="OnaniFrontend/static",
    template_folder="OnaniFrontend/templates",
)
app.config[
    "SECRET_KEY"
] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"  # Temporary; Change to config generated one
onaniDB = DatabaseController(pymongo.MongoClient("mongodb://localhost:27017/"))
sockets = Sockets(app)


logger = logging.getLogger("OnaniCore")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# @login_manager.user_loader
# def user_loader(username):
#     user_check = system.database.get_user(username)
#     if user_check is None:
#         return
#     user = User()
#     user.id = user_check["username"]
#     user.is_admin = user_check["is_admin"]
#     user.api_key = user_check["api_key"]
#     user.favourites = user_check["favourites"]
#     user.settings = dict(system.default_user_settings)
#     user.settings.update(user_check["settings"])
#     return user


@app.route("/")
def index():
    onaniDB.add_user(username="Blakeando", password="test", permissions=666)
    print(onaniDB.get_user(id=1))
    return render_template("/index.html")


if __name__ == "__main__":
    app.run()
