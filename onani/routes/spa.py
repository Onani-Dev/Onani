# -*- coding: utf-8 -*-
"""SPA blueprint — serves the Vue application's index.html for all non-API routes."""
import os

from flask import Blueprint, abort, current_app, request, send_file, send_from_directory
from onani.models import ExternalLibrary, Post

from onani.services.files import (
    build_cached_image_variant,
    parse_thumbnail_size,
    shard_path,
)

_VIDEO_EXTS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}

_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

spa_bp = Blueprint("spa", __name__, static_folder=_dist_dir, static_url_path="/spa-static")


def _safe_path_part(value: str) -> str:
    if not value or "/" in value or "\\" in value or ".." in value:
        abort(404)
    return value


def _is_enabled(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "on"}
    return bool(value)


def _resolve_external_path(library_name: str, relative_path: str) -> str:
    if not relative_path or relative_path.startswith("/"):
        abort(404)

    library = None
    if library_name.isdigit():
        library = ExternalLibrary.query.get(int(library_name))
    if library is None:
        library = ExternalLibrary.query.filter_by(name=library_name).first()
    if library is None or not _is_enabled(library.enabled):
        abort(404)

    rel_norm = os.path.normpath(relative_path).lstrip("/\\")
    if rel_norm.startswith("..") or rel_norm in ("", "."):
        abort(404)

    root = os.path.normpath(library.path)
    resolved = os.path.normpath(os.path.join(root, rel_norm))
    if resolved != root and not resolved.startswith(root + os.sep):
        abort(404)

    if not os.path.isfile(resolved):
        abort(404)
    return resolved


def _resolve_post_source_path(filename: str) -> str | None:
    images_dir = current_app.config.get("IMAGES_DIR", "/images")
    local_path = shard_path(images_dir, filename)
    if os.path.isfile(local_path):
        return local_path

    post = Post.query.filter_by(filename=filename, is_external=True).first()
    if post is None or not post.library_file:
        return None

    library = post.library_file.library
    if library is None or not _is_enabled(library.enabled):
        return None

    candidate = post.library_file.file_path
    return candidate if candidate and os.path.isfile(candidate) else None


@spa_bp.route("/external/<library_name>/<path:relative_path>")
def external_file(library_name: str, relative_path: str):
    path = _resolve_external_path(library_name, relative_path)
    return send_file(path, conditional=True)


@spa_bp.route("/images/<shard>/<filename>")
def image_file(shard: str, filename: str):
    shard = _safe_path_part(shard)
    filename = _safe_path_part(filename)
    if not filename.startswith(shard):
        abort(404)

    path = _resolve_post_source_path(filename)
    if not path:
        abort(404)
    return send_file(path, conditional=True)


@spa_bp.route("/avatars/<filename>")
def avatar_file(filename: str):
    filename = _safe_path_part(filename)
    avatars_dir = current_app.config.get("AVATARS_DIR", "/avatars")
    path = os.path.join(avatars_dir, filename)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, conditional=True)


@spa_bp.route("/images/thumbnail/<shard>/<filename>")
def image_thumbnail(shard: str, filename: str):
    shard = _safe_path_part(shard)
    filename = _safe_path_part(filename)
    if not filename.startswith(shard):
        abort(404)

    images_dir = current_app.config.get("IMAGES_DIR", "/images")
    source_path = _resolve_post_source_path(filename)
    if not source_path:
        abort(404)

    size_px = parse_thumbnail_size(request.args.get("size"), default=150)
    cached = build_cached_image_variant(
        source_path=source_path,
        cache_root=images_dir,
        source_filename=filename,
        variant="images",
        max_width=size_px,
        max_height=size_px,
        quality=50,
    )
    return send_file(cached, conditional=True)


@spa_bp.route("/videos/thumbnail/<shard>/<filename>")
def video_thumbnail(shard: str, filename: str):
    shard = _safe_path_part(shard)
    filename = _safe_path_part(filename)
    if not filename.startswith(shard):
        abort(404)

    images_dir = current_app.config.get("IMAGES_DIR", "/images")
    # Video thumbnails are stored as extracted JPEG frames using the video's stem
    source_path = shard_path(images_dir, filename)
    if not os.path.isfile(source_path):
        abort(404)

    size_px = parse_thumbnail_size(request.args.get("size"), default=150)
    cached = build_cached_image_variant(
        source_path=source_path,
        cache_root=images_dir,
        source_filename=filename,
        variant="videos",
        max_width=size_px,
        max_height=size_px,
        quality=50,
    )
    return send_file(cached, conditional=True)


@spa_bp.route("/avatars/thumbnail/<filename>")
def avatar_thumbnail(filename: str):
    filename = _safe_path_part(filename)
    avatars_dir = current_app.config.get("AVATARS_DIR", "/avatars")
    source_path = os.path.join(avatars_dir, filename)
    if not os.path.isfile(source_path):
        abort(404)

    size_px = parse_thumbnail_size(request.args.get("size"), default=150)
    cached = build_cached_image_variant(
        source_path=source_path,
        cache_root=avatars_dir,
        source_filename=filename,
        variant="avatars",
        max_width=size_px,
        max_height=size_px,
        quality=50,
    )
    return send_file(cached, conditional=True)


@spa_bp.route("/sample/<shard>/<filename>")
def sample_image(shard: str, filename: str):
    shard = _safe_path_part(shard)
    filename = _safe_path_part(filename)
    if not filename.startswith(shard):
        abort(404)

    images_dir = current_app.config.get("IMAGES_DIR", "/images")
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    source_name = filename
    source_path = _resolve_post_source_path(source_name)

    if ext in _VIDEO_EXTS:
        stem = filename.rsplit(".", 1)[0]
        source_name = f"{stem}.jpg"
        source_path = _resolve_post_source_path(source_name)

    if not source_path:
        abort(404)

    cached = build_cached_image_variant(
        source_path=source_path,
        cache_root=images_dir,
        source_filename=source_name,
        variant="sample",
        max_width=800,
        max_height=2000,
        quality=80,
    )
    return send_file(cached, conditional=True)


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
