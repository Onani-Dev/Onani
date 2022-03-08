# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 00:25:11
import os

# Flask Config
STATIC_PATH = "/static/"
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

if SECRET_KEY == "dev":
    print(
        "Warning! SECRET_KEY is not set. Make sure to run 'python generate.py' before starting Onani."
    )

# SQLAlchemy Config
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://onani_db:{os.environ['DB_PASSWORD']}@postgres:5432/onani_db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
