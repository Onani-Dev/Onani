# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-24 08:29:17
import os

# Flask Config
STATIC_PATH = "/static/"
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
TESTING = bool(os.environ.get("TESTING", False))

# SQLAlchemy Config
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://onani_db:{os.environ['DB_PASSWORD']}@postgres:5432/onani_db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False  # WHY are you not disabled by default

SQLALCHEMY_ECHO = bool(os.environ.get("FLASK_SQLALCHEMY_ECHO"))

# Recaptcha
RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]
RECAPTCHA_DATA_ATTRS = {"theme": "dark"}

# Cookie settings
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "strict"
PREFERRED_URL_SCHEME = "https"

# Onani settings
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

# ADMIN ONLY SETTINGS
PER_PAGE_ERRORS = 30

# Celery
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
CELERY_BROKER_URL = "redis://redis:6379/1"

# Flask Limiter
RATELIMIT_ENABLED = True
RATELIMIT_STORAGE_URI = "redis://redis:6379/0"
