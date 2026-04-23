# -*- coding: utf-8 -*-
import os

from flask import Flask, request
from flask_celeryext import FlaskCeleryExt
from flask_crontab import Crontab
from flask_limiter import Limiter
from flask_login import LoginManager, current_user
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
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


def init_app():
    frontend_static_dir = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "public", "static"
    )
    app = Flask(
        __name__,
        static_url_path="/static/",
        static_folder=frontend_static_dir,
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    app.config.from_pyfile("./config.py")

    app.url_map.strict_slashes = False

    from .cron import tasks
    from .routes import main_api
    from .routes.spa import spa_bp

    # Vue SPA — catch-all, must be registered first so API prefix takes priority
    app.register_blueprint(spa_bp)

    # REST API
    app.register_blueprint(main_api, url_prefix="/api")

    crontab.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    ext.init_app(app)
    # Allow pool_restart broadcast (used by the admin "Restart Celery" task).
    ext.celery.conf.worker_pool_restarts = True
    limiter.init_app(app)
    login_manager.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    @login_manager.unauthorized_handler
    def _unauthorized():
        if request.path.startswith("/api/"):
            return {"message": "Authentication required."}, 401
        # For non-API paths the SPA handles routing; return the SPA index
        from .routes.spa import spa_index
        return spa_index("")

    @app.errorhandler(Exception)
    def _error_handler(e):
        import traceback
        from werkzeug.exceptions import HTTPException
        from .controllers.database.errors import log_error

        code = e.code if isinstance(e, HTTPException) else 500
        if app.testing:
            print(traceback.print_tb(e.__traceback__))
        if code == 500:
            error = log_error(e)
            return {"message": "Internal server error.", "error_id": str(error.id) if error else None}, 500
        return {"message": getattr(e, "description", str(e))}, code

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
                owner = create_user(
                    username="admin",
                    password=default_pw,
                    role=UserRoles.OWNER,
                )
                owner.permissions = UserPermissions.ADMINISTRATION
                db.session.commit()
                app.logger.warning(
                    "Created default admin account (username: admin). "
                    "Change the password immediately!"
                )
            else:
                owners = User.query.filter_by(role=UserRoles.OWNER).all()
                for owner in owners:
                    if owner.permissions != UserPermissions.ADMINISTRATION:
                        owner.permissions = UserPermissions.ADMINISTRATION
                        db.session.commit()
        except Exception:
            pass

    # ── CLI: migrate flat image/video files to sharded layout ────────────
    @app.cli.command("migrate-images")
    def migrate_images_command():
        """Move existing flat-directory image/video files into the sharded layout.

        Files are relocated from  <IMAGES_DIR>/<filename>
        to                        <IMAGES_DIR>/<first-2-hex-chars>/<filename>

        Safe to re-run: files already in the correct location are skipped.
        """
        import shutil
        from .services.files import shard_path

        images_dir = app.config.get("IMAGES_DIR", "/images")
        moved = skipped = failed = 0

        for entry in os.scandir(images_dir):
            if not entry.is_file():
                continue  # skip subdirectories (already sharded)
            filename = entry.name
            # Skip hidden / non-hash files (e.g. .gitkeep)
            if len(filename) < 2 or not filename[0:2].isalnum():
                continue
            dest = shard_path(images_dir, filename)
            if os.path.exists(dest):
                # Already migrated — remove the flat copy if it still exists
                try:
                    os.remove(entry.path)
                    skipped += 1
                except OSError:
                    skipped += 1
                continue
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(entry.path, dest)
                moved += 1
            except Exception as exc:
                print(f"  ERROR moving {filename}: {exc}")
                failed += 1

        print(f"migrate-images done — moved: {moved}  skipped: {skipped}  failed: {failed}")

    return app

