# -*- coding: utf-8 -*-
"""SPA blueprint — serves the Vue application's index.html for all non-API routes."""
import os

from flask import Blueprint, send_from_directory

_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

spa_bp = Blueprint("spa", __name__, static_folder=_dist_dir, static_url_path="/spa-static")


@spa_bp.route("/", defaults={"_path": ""})
@spa_bp.route("/<path:_path>")
def spa_index(_path: str):
    """Serve the Vue SPA index.html as a catch-all."""
    index = os.path.join(_dist_dir, "index.html")
    if os.path.exists(index):
        return send_from_directory(_dist_dir, "index.html")
    # During development before the frontend is built, return a placeholder
    return (
        "<html><body><h1>Frontend not built yet.</h1>"
        "<p>Run <code>cd frontend && npm install && npm run build</code></p></body></html>",
        200,
    )
