# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:29:14
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-22 19:29:55

import datetime
import html
import os
import time

import emoji
import humanize
from flask import Flask, request
from flask_celeryext import FlaskCeleryExt
from flask_crontab import Crontab
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_qrcode import QRcode
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

crontab = Crontab()
csrf = CSRFProtect()
db = SQLAlchemy()
ext = FlaskCeleryExt()
limiter = Limiter(
    key_func=lambda: (
        current_user.login_id
        if current_user.is_authenticated
        else (request.remote_addr or "127.0.0.1")
    ),
    default_limits=[
        "100 per minute",
    ],
)
login_manager = LoginManager()
ma = Marshmallow()
migrate = Migrate()
celery = ext.celery
qr = QRcode()

from Onani.controllers.utils import complete_file_url, is_url, url_hostname


def init_app():
    app = Flask(__name__, static_url_path="/static/", static_folder="static")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2)

    app.config.from_pyfile("./config.py")

    # Make it so it ignores trailing slashes in URL
    app.url_map.strict_slashes = False

    app.jinja_env.globals.update(
        datetime=datetime,
        time=time,
        emoji=emoji,
        humanize=humanize,
        html=html,
        complete_file_url=complete_file_url,
        is_url=is_url,
        url_hostname=url_hostname,
    )

    from .cron import tasks
    from .routes import admin, atom, main, main_api, rss
    from .routes.spa import spa_bp

    # Vue SPA — served at /
    app.register_blueprint(spa_bp)

    # Main API routes
    app.register_blueprint(main_api, url_prefix="/api")

    # Legacy server-rendered routes (kept during SPA transition)
    app.register_blueprint(main)

    # Admin routes
    app.register_blueprint(admin, url_prefix="/admin")

    # Rss and atom feed routes
    app.register_blueprint(atom, url_prefix="/atom")
    app.register_blueprint(rss, url_prefix="/rss")

    crontab.init_app(app)  # flask crontab init
    csrf.init_app(app)  # CSRF Protection init
    db.init_app(app)  # SQLAlchemy init
    ext.init_app(app)  # Celery init
    limiter.init_app(app)  # Flask limiter init
    login_manager.login_view = "main.login"
    login_manager.init_app(app)  # login manager init
    ma.init_app(app)  # Marshmallow init
    migrate.init_app(app, db)  # flask migrate init
    qr.init_app(app)  # Qr init
    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)
        except ImportError:
            pass

    # Create a default admin account on first startup if none exist
    with app.app_context():
        from .models import User, UserPermissions
        from .models.user.roles import UserRoles
        try:
            if User.query.count() == 0:
                from .services.users import create_user
                default_pw = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin")
                admin = create_user(
                    username="admin",
                    password=default_pw,
                    role=UserRoles.OWNER,
                )
                admin.permissions = UserPermissions.ADMINISTRATION
                db.session.commit()
                app.logger.warning(
                    "Created default admin account (username: admin). "
                    "Change the password immediately!"
                )
            else:
                # Ensure OWNER accounts have full permissions
                owners = User.query.filter_by(role=UserRoles.OWNER).all()
                for owner in owners:
                    if owner.permissions != UserPermissions.ADMINISTRATION:
                        owner.permissions = UserPermissions.ADMINISTRATION
                        db.session.commit()
        except Exception:
            # Table may not exist yet (first migration)
            pass

    # Line belows prints all the registered routes, useful to debug
    # if app.testing:
    #     print(app.url_map)  # Then why is it not????
    # i see why.
    return app
