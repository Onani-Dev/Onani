# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-25 15:29:22

import datetime
import time

import emoji
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO

socketio = SocketIO()
login_manager = LoginManager()


def init_app():
    app = Flask(__name__, static_url_path="")
    # Temporary secret key; Change to config generated one
    app.config["SECRET_KEY"] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    app.jinja_env.globals.update(datetime=datetime, time=time, emoji=emoji)

    from .main import main as main_blueprint
    from .main import main_api

    app.register_blueprint(main_blueprint)
    app.register_blueprint(main_api, url_prefix="/api")

    socketio.init_app(app)
    login_manager.init_app(app)
    return app
