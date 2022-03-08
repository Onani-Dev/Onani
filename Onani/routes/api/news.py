# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:02:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 03:03:37
from flask import jsonify
from Onani.models import NewsPost, NewsPostSchema

from . import main_api


@main_api.route("/news", methods=["GET"])
def get_news():
    news_schema = NewsPostSchema(many=True)
    news = NewsPost.query.order_by(NewsPost.id.desc()).limit(10)
    return jsonify(news_schema.dump(news))
