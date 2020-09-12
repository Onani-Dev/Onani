# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-12 16:13:34

import os

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO

socketio = SocketIO()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, static_url_path="")
    # Temporary secret key; Change to config generated one
    app.config["SECRET_KEY"] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    socketio.init_app(app)
    login_manager.init_app(app)
    return app
