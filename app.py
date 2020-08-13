# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-14 00:10:21

import logging
import os

import pymongo
from flask import Flask
from flask_sockets import Sockets

import OnaniCore

app = Flask(__name__)
app.config[
    "SECRET_KEY"
] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"  # Temporary; Change to config generated one
onaniDB = OnaniCore.DatabaseController(
    pymongo.MongoClient("mongodb://localhost:27017/")
)
sockets = Sockets(app)


@app.route("/")
def index():
    return "Hello world"


if __name__ == "__main__":
    app.run()
