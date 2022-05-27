# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 18:16:18

import datetime
import html
import time

import emoji
import humanize
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

csrf = CSRFProtect()
db = SQLAlchemy()
ext = FlaskCeleryExt()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        "100 per minute",
    ],
)
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()
celery = ext.celery


def init_app():
    app = Flask(__name__, static_url_path="/static/", static_folder="/static")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)

    app.config.from_pyfile("./config.py")

    app.jinja_env.globals.update(
        datetime=datetime, time=time, emoji=emoji, humanize=humanize, html=html
    )

    from .routes import admin, atom, main, main_api, rss

    # Main Routes
    app.register_blueprint(main)

    # Main API routes
    app.register_blueprint(main_api, url_prefix="/api")

    # Admin api Routes
    # admin.register_blueprint(admin_api, url_prefix="/api")

    # Admin routes
    app.register_blueprint(admin, url_prefix="/admin")

    # Rss and atom feed routes
    app.register_blueprint(atom, url_prefix="/atom")
    app.register_blueprint(rss, url_prefix="/rss")

    csrf.init_app(app)  # CSRF Protection init
    db.init_app(app)  # SQLAlchemy init
    ext.init_app(app)  # Celery init
    limiter.init_app(app)  # Flask limiter init
    login_manager.init_app(app)  # login manager init
    ma.init_app(app)  # Marshmallow init
    migrate.init_app(app, db)  # flask migrate init

    # Line belows prints all the registered routes, useful to debug
    # if app.testing:
    #     print(app.url_map)  # Then why is it not????
    # i see why.
    return app
