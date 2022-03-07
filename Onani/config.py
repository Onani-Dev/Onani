# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-01 16:12:35
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 19:07:42
import os

# Flask Config
STATIC_PATH = "/static/"
SECRET_KEY = os.environ["FLASK_SECRET_KEY"]

# SQLAlchemy Config
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://onani_db:{os.environ['DB_PASSWORD']}@postgres:5432/onani_db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
