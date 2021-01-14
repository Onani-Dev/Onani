# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-12 17:56:47

import datetime
import time
import emoji

from flask import Flask
from flask_login import LoginManager

from flask_sqlalchemy import SQLAlchemy

login_manager = LoginManager()
db = SQLAlchemy()  # session_options={"autocommit": True}


def init_app():
    app = Flask(__name__, static_url_path="")

    app.config["SECRET_KEY"] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"
    # Temporary secret key; Change to config generated one

    app.config.from_pyfile("config.py")

    app.jinja_env.globals.update(datetime=datetime, time=time, emoji=emoji)

    from .routes import main, api

    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix="/api")

    login_manager.init_app(app)  # login manager init
    db.init_app(app)  # MongoEngine init

    return app
