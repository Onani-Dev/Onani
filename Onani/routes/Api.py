# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-05 01:56:58
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-05 03:32:59

import json
from flask import flash, jsonify, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from Onani.models import NewsPost, NewsPostSchema

from . import api, db


@api.route("/", methods=["GET"])
def api_index():
    return jsonify({"message": "allo!"})


@api.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    pass


@api.route("/news", methods=["GET"])
def get_news():
    news_schema = NewsPostSchema(many=True)
    news = NewsPost.query.order_by(NewsPost.id.desc()).limit(10)
    return jsonify(news_schema.dump(news))
