# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-05 01:52:03
import os

# Flask Config
STATIC_PATH = "/static/"
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
TESTING = bool(os.environ.get("TESTING", False))

if SECRET_KEY == "dev":
    print(
        "Warning! SECRET_KEY is not set. Make sure to run 'python generate.py' before starting Onani."
    )


# SQLAlchemy Config
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://onani_db:{os.environ['DB_PASSWORD']}@postgres:5432/onani_db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

if os.environ.get("FLASK_SQLALCHEMY_ECHO"):
    print("SQLALCHEMY_ECHO enabled.")
    SQLALCHEMY_ECHO = True


# Recaptcha
RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]
RECAPTCHA_DATA_ATTRS = {"theme": "dark"}
