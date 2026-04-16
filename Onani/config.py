# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-22 21:15:34
import os

# Flask Config
STATIC_PATH = "/static/"
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
TESTING = os.getenv("TESTING", "").lower() == "true"

# SQLAlchemy Config
# DATABASE_URL env var overrides the default Postgres URI (useful for testing with SQLite)
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    f"postgresql://onani_db:{os.environ['DB_PASSWORD']}@postgres:5432/onani_db",
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ECHO = bool(os.environ.get("FLASK_SQLALCHEMY_ECHO"))



# Cookie settings
SESSION_COOKIE_SECURE = not TESTING and os.environ.get("FLASK_ENV") != "development"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"

# File storage paths (inside container)
IMAGES_DIR = os.environ.get("IMAGES_DIR", "/images")
AVATARS_DIR = os.environ.get("AVATARS_DIR", "/avatars")

# Max upload size: 50 MB
MAX_CONTENT_LENGTH = 50 * 1024 * 1024

# Onani settings
POST_MIN_TAGS = 10
TAG_CHAR_LIMIT = 64
PER_PAGE_POSTS = 90
PER_PAGE_USER_POSTS = 50
PER_PAGE_USERS = 30
PER_PAGE_NEWS = 30
PER_PAGE_COLLECTIONS = 80
PER_PAGE_TAGS = 30

# API Settings
API_PER_PAGE_COMMENTS = 30
API_PER_PAGE_TAGS = 30
API_PER_PAGE_NEWS = 30
API_PER_PAGE_POSTS = 30
API_AUTOCOMPLETE_LIMIT = 10
API_MAX_PER_PAGE = 100

# ADMIN ONLY SETTINGS
PER_PAGE_ERRORS = 30

# Celery
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")

# Flask Limiter
RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "True").lower() != "false"
RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "redis://redis:6379/0")
RATELIMIT_HEADERS_ENABLED = True

# Flask Restful
BUNDLE_ERRORS = True

# Flask debugtoolbar
DEBUG_TB_INTERCEPT_REDIRECTS = False

# gallery-dl
# Optional path to a gallery-dl config.json for per-site credentials/cookies.
# See: https://github.com/mikf/gallery-dl#configuration
GALLERY_DL_CONFIG_FILE = os.environ.get("GALLERY_DL_CONFIG_FILE")
