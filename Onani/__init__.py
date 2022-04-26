# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-26 01:09:17

import datetime
import time

import emoji
import humanize
from flask import Flask
from flask_dramatiq import Dramatiq
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

csrf = CSRFProtect()
db = SQLAlchemy()  # session_options={"autocommit": True}
dramatiq = Dramatiq()
limiter = Limiter(key_func=lambda: current_user.login_id)
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()

from .tasks import test


def init_app():
    app = Flask(__name__, static_url_path="/static/", static_folder="/static")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    app.config.from_pyfile("./config.py")

    app.jinja_env.globals.update(
        datetime=datetime, time=time, emoji=emoji, humanize=humanize
    )

    from .routes import admin, admin_api, atom, main, main_api, rss

    app.register_blueprint(main)
    app.register_blueprint(main_api, url_prefix="/api")
    admin.register_blueprint(admin_api, url_prefix="/api")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(atom, url_prefix="/atom")
    app.register_blueprint(rss, url_prefix="/rss")

    csrf.init_app(app)  # CSRF Protection init
    db.init_app(app)  # SQLAlchemy init
    dramatiq.init_app(app)  # dramatiq init
    limiter.init_app(app)  # Flask limiter init
    login_manager.init_app(app)  # login manager init
    ma.init_app(app)  # Marshmallow init
    migrate.init_app(app, db)  # flask migrate init

    # Line belows prints all the registered routes, useful to debug
    if app.testing:
        print(app.url_map)  # Then why is it not????

    return app
