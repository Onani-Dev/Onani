# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:02:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-16 00:17:00
from flask import abort, jsonify, request
from Onani.models import NewsPost, NewsPostSchema

from . import main_api, make_api_response


@main_api.route("/news", methods=["GET"])
def get_news():
    # Single query
    if id := request.args.get("id"):
        if not id.isdigit():
            abort(400)
        news = NewsPost.query.filter_by(id=int(id)).first_or_404()
        return make_api_response({"data": NewsPostSchema().dump(news)})

    # Multiple query
    page = request.args.get("page", "0")
    per_page = request.args.get("per_page", "10")

    page = int(page) if page.isdigit() else 0
    per_page = int(per_page) if per_page.isdigit() else 10

    news = NewsPost.query.order_by(NewsPost.id.desc()).paginate(
        per_page=per_page, page=page, error_out=False
    )

    return make_api_response(
        {
            "data": NewsPostSchema(many=True).dump(news.items),
            "next_page": news.next_num,
            "prev_page": news.prev_num,
            "total": news.total,
        }
    )
