# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-22 21:15:34
import os

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]  # pip install tomli on Python < 3.11
    except ImportError:
        tomllib = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Optional TOML config file support
#
# Point ONANI_CONFIG to a TOML file to configure the app without env vars:
#   ONANI_CONFIG=/etc/onani/onani.toml
#
# Precedence (highest to lowest): env vars > TOML file > built-in defaults
# ---------------------------------------------------------------------------
_toml: dict = {}
_config_path = os.environ.get("ONANI_CONFIG")
if _config_path:
    if tomllib is None:
        raise RuntimeError(
            "ONANI_CONFIG is set but no TOML parser is available. "
            "On Python < 3.11 install tomli: pip install tomli"
        )
    with open(_config_path, "rb") as _f:
        _toml = tomllib.load(_f)


def _t(section: str, key: str, default=None):
    """Return the value from the TOML config, falling back to *default*."""
    return _toml.get(section, {}).get(key, default)


def _bool(env_var: str, section: str, key: str, default: bool) -> bool:
    """Resolve a boolean setting: env var > TOML > default.

    Any env var value other than the string "false" (case-insensitive) is
    treated as True.
    """
    val = os.environ.get(env_var)
    if val is not None:
        return val.lower() != "false"
    toml_val = _toml.get(section, {}).get(key)
    if toml_val is not None:
        return bool(toml_val)
    return default


# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
STATIC_PATH = "/static/"

SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or _t("flask", "secret_key")
if not SECRET_KEY:
    raise RuntimeError(
        "Flask secret key is not configured. "
        "Set the FLASK_SECRET_KEY environment variable, "
        "or set secret_key under [flask] in your ONANI_CONFIG file."
    )

TESTING = os.getenv("TESTING", "").lower() == "true"

# ---------------------------------------------------------------------------
# SQLAlchemy
# ---------------------------------------------------------------------------
_db_password = os.environ.get("DB_PASSWORD") or _t("database", "password")
_db_url_default = (
    f"postgresql://onani_db:{_db_password}@postgres:5432/onani_db"
    if _db_password
    else None
)

SQLALCHEMY_DATABASE_URI = (
    os.environ.get("DATABASE_URL") or _t("database", "url") or _db_url_default
)
if not SQLALCHEMY_DATABASE_URI:
    raise RuntimeError(
        "Database URL is not configured. "
        "Set DATABASE_URL or DB_PASSWORD env var, "
        "or set url / password under [database] in your ONANI_CONFIG file."
    )

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Pool pre-ping validates each connection before use, discarding ones left in
# a bad state after connection errors or aborted transactions.  Critical for
# long-running Celery workers doing bulk imports where individual post saves
# can fail and leave connections in an aborted-transaction state.
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": int(
        os.environ.get("SQLALCHEMY_POOL_RECYCLE") or _t("database", "pool_recycle", 3600)
    ),
}

SQLALCHEMY_ECHO = _bool("FLASK_SQLALCHEMY_ECHO", "database", "echo", False)

# ---------------------------------------------------------------------------
# Cookie / session settings
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", "cookies", "secure", True)
SESSION_COOKIE_HTTPONLY = _bool("SESSION_COOKIE_HTTPONLY", "cookies", "httponly", True)
SESSION_COOKIE_SAMESITE = (
    os.environ.get("SESSION_COOKIE_SAMESITE") or _t("cookies", "samesite", "strict")
)
PREFERRED_URL_SCHEME = (
    os.environ.get("PREFERRED_URL_SCHEME") or _t("cookies", "preferred_scheme", "https")
)

# ---------------------------------------------------------------------------
# File storage paths (inside container)
# ---------------------------------------------------------------------------
IMAGES_DIR = os.environ.get("IMAGES_DIR") or _t("storage", "images_dir", "/images")
AVATARS_DIR = os.environ.get("AVATARS_DIR") or _t("storage", "avatars_dir", "/avatars")
MAX_CONTENT_LENGTH = (
    int(os.environ.get("MAX_UPLOAD_MB") or _t("storage", "max_upload_mb", 50)) * 1024 * 1024
)

# ---------------------------------------------------------------------------
# Content settings
# ---------------------------------------------------------------------------
POST_MIN_TAGS = int(os.environ.get("POST_MIN_TAGS") or _t("content", "post_min_tags", 10))
TAG_CHAR_LIMIT = int(os.environ.get("TAG_CHAR_LIMIT") or _t("content", "tag_char_limit", 64))

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
PER_PAGE_USER_POSTS = int(os.environ.get("PER_PAGE_USER_POSTS") or _t("pagination", "user_posts", 50))
PER_PAGE_USERS = int(os.environ.get("PER_PAGE_USERS") or _t("pagination", "users", 30))
PER_PAGE_COLLECTIONS = int(os.environ.get("PER_PAGE_COLLECTIONS") or _t("pagination", "collections", 80))
API_PER_PAGE_POSTS = int(os.environ.get("API_PER_PAGE_POSTS") or _t("pagination", "posts", 30))
API_PER_PAGE_COMMENTS = int(os.environ.get("API_PER_PAGE_COMMENTS") or _t("pagination", "comments", 30))
API_PER_PAGE_TAGS = int(os.environ.get("API_PER_PAGE_TAGS") or _t("pagination", "tags", 30))
API_PER_PAGE_NEWS = int(os.environ.get("API_PER_PAGE_NEWS") or _t("pagination", "news", 30))
API_AUTOCOMPLETE_LIMIT = int(os.environ.get("API_AUTOCOMPLETE_LIMIT") or _t("pagination", "autocomplete_limit", 10))
API_MAX_PER_PAGE = int(os.environ.get("API_MAX_PER_PAGE") or _t("pagination", "max_per_page", 100))

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_RESULT_BACKEND = (
    os.environ.get("CELERY_RESULT_BACKEND")
    or _t("celery", "result_backend", "redis://redis:6379/1")
)
CELERY_BROKER_URL = (
    os.environ.get("CELERY_BROKER_URL")
    or _t("celery", "broker_url", "redis://redis:6379/1")
)

# ---------------------------------------------------------------------------
# Flask-Limiter
# ---------------------------------------------------------------------------
RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", "rate_limit", "enabled", True)
RATELIMIT_STORAGE_URI = (
    os.environ.get("RATELIMIT_STORAGE_URI")
    or _t("rate_limit", "storage_uri", "redis://redis:6379/0")
)
RATELIMIT_HEADERS_ENABLED = True

# ---------------------------------------------------------------------------
# Flask-RESTful
# ---------------------------------------------------------------------------
BUNDLE_ERRORS = True

# ---------------------------------------------------------------------------
# Flask DebugToolbar
# ---------------------------------------------------------------------------
DEBUG_TB_INTERCEPT_REDIRECTS = False

# ---------------------------------------------------------------------------
# gallery-dl
# ---------------------------------------------------------------------------
# Optional path to a gallery-dl config.json for per-site credentials/cookies.
# See: https://github.com/mikf/gallery-dl#configuration
GALLERY_DL_CONFIG_FILE = (
    os.environ.get("GALLERY_DL_CONFIG_FILE") or _t("gallery_dl", "config_file") or None
)

# How long (seconds) to wait for a single gallery-dl job before giving up.
# Large accounts (Reddit, Twitter) with hundreds of posts need several minutes.
GALLERY_DL_JOB_TIMEOUT = int(
    os.environ.get("GALLERY_DL_JOB_TIMEOUT") or _t("gallery_dl", "job_timeout", 600)
)

# Per-request HTTP timeout passed to gallery-dl extractors.
GALLERY_DL_HTTP_TIMEOUT = float(
    os.environ.get("GALLERY_DL_HTTP_TIMEOUT") or _t("gallery_dl", "http_timeout", 20)
)

# How many times gallery-dl will retry a failed HTTP request.
GALLERY_DL_RETRIES = int(
    os.environ.get("GALLERY_DL_RETRIES") or _t("gallery_dl", "retries", 2)
)

# Rate-limit sleep bounds (seconds) passed to gallery-dl.
# Lower values speed up paginated imports; raise them if sites throttle aggressively.
GALLERY_DL_WAIT_MIN = float(
    os.environ.get("GALLERY_DL_WAIT_MIN") or _t("gallery_dl", "wait_min", 0.5)
)
GALLERY_DL_WAIT_MAX = float(
    os.environ.get("GALLERY_DL_WAIT_MAX") or _t("gallery_dl", "wait_max", 3.0)
)

# Maximum number of posts to fetch from a single gallery-dl job.
# Limits gallery-dl's image-range so search pages with thousands of results
# don't block the worker for the entire job timeout.  0 = no limit.
GALLERY_DL_MAX_POSTS = int(
    os.environ.get("GALLERY_DL_MAX_POSTS") or _t("gallery_dl", "max_posts", 200)
)

# Maximum posts for search/list pages (tag searches, listings, feeds).
# Kept lower than GALLERY_DL_MAX_POSTS because these URLs are highly paginated
# and can otherwise spend the entire timeout in metadata scraping.
GALLERY_DL_MAX_POSTS_SEARCH = int(
    os.environ.get("GALLERY_DL_MAX_POSTS_SEARCH") or _t("gallery_dl", "max_posts_search", 50)
)

# ---------------------------------------------------------------------------
# DeepDanbooru
# ---------------------------------------------------------------------------
DEEPDANBOORU_ENABLED = _bool("DEEPDANBOORU_ENABLED", "deepdanbooru", "enabled", False)
DEEPDANBOORU_PROJECT_PATH = (
    os.environ.get("DEEPDANBOORU_PROJECT_PATH") or _t("deepdanbooru", "project_path") or None
)
DEEPDANBOORU_MODEL_PATH = (
    os.environ.get("DEEPDANBOORU_MODEL_PATH") or _t("deepdanbooru", "model_path") or None
)
DEEPDANBOORU_TAGS_PATH = (
    os.environ.get("DEEPDANBOORU_TAGS_PATH") or _t("deepdanbooru", "tags_path") or None
)
DEEPDANBOORU_THRESHOLD = float(
    os.environ.get("DEEPDANBOORU_THRESHOLD") or _t("deepdanbooru", "threshold", 0.5)
)
DEEPDANBOORU_COMPILE_MODEL = _bool(
    "DEEPDANBOORU_COMPILE_MODEL", "deepdanbooru", "compile_model", False
)
DEEPDANBOORU_ALLOW_GPU = _bool(
    "DEEPDANBOORU_ALLOW_GPU", "deepdanbooru", "allow_gpu", False
)
DEEPDANBOORU_MAX_TAGS = int(
    os.environ.get("DEEPDANBOORU_MAX_TAGS") or _t("deepdanbooru", "max_tags", 24)
)
