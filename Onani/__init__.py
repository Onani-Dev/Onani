# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-28 22:04:49

import datetime
import time

import dramatiq
import emoji
import humanize
from dramatiq.brokers.redis import RedisBroker
from dramatiq.encoder import PickleEncoder
from dramatiq.middleware import default_middleware
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from flask import Flask
from flask_dramatiq import AppContextMiddleware
from flask_dramatiq import Dramatiq as _Dramatiq
from flask_dramatiq import warn
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import DRAMATIQ_BROKER_URL

csrf = CSRFProtect()
db = SQLAlchemy()  # session_options={"autocommit": True}
limiter = Limiter(key_func=lambda: current_user.login_id)
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()


result_backend = RedisBackend(url=DRAMATIQ_BROKER_URL, encoder=PickleEncoder)
broker = RedisBroker(
    url=DRAMATIQ_BROKER_URL, middleware=[m() for m in default_middleware]
)
broker.add_middleware(Results(backend=result_backend))
# set global broker
dramatiq.set_broker(broker)


class Dramatiq(_Dramatiq):
    def __init__(self, *args, **kwargs):
        super(Dramatiq, self).__init__(*args, **kwargs)
        self.result_backend = result_backend
        self.broker = broker

    def init_app(self, app):
        if self.app is not None:
            warn(
                "%s is used by more than one flask application. "
                "Actor's context may be set incorrectly." % (self,),
                stacklevel=2,
            )
        self.app = app
        app.extensions[f"dramatiq-{self.name}"] = self
        app.config.setdefault(self.config_prefix, self.broker_cls)

        # only initialize once
        if not isinstance(self.broker.middleware[0], AppContextMiddleware):
            self.broker.add_middleware(
                AppContextMiddleware(app), before=self.middleware[0].__class__
            )

        for actor in self.actors:
            actor.register(broker=self.broker)

    def get_result(self, message, *args, **kwargs):
        return message.get_result(backend=self.result_backend, *args, **kwargs)

    def store_actor(self, fn=None, **kw):
        return self.actor(fn=None, **kw)


dramatiq = Dramatiq()
# Import Dramatiq Tasks
from .tasks import test


def init_app():
    app = Flask(__name__, static_url_path="/static/", static_folder="/static")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    # dramatiq.broker.add_middleware(AppContextMiddleware(app))
    # dramatiq.broker.add_middleware(
    #     Results(backend=RedisBackend(url=DRAMATIQ_BROKER_URL, encoder=PickleEncoder))
    # )

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
