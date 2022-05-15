# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-15 15:04:53
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 15:52:31
from flask import current_app
from flask_restful import Resource, reqparse
from Onani.models import NewsPost, NewsPostSchema

from . import api


class News(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument(
            "page", location="args", type=int, required=False, default=0
        )

        parser.add_argument(
            "per_page",
            location="args",
            type=int,
            required=False,
            default=current_app.config["API_PER_PAGE_NEWS"],
        )

        parser.add_argument("id", location="args", type=int, default=None)

        # Parse request args
        args = parser.parse_args()

        # Single news article
        if args["id"]:
            news = NewsPost.query.filter_by(id=args["id"]).first_or_404()
            return NewsPostSchema().dump(news)

        # Multiple news
        news = NewsPost.query.order_by(NewsPost.id.desc()).paginate(
            per_page=args["per_page"], page=args["page"], error_out=False
        )
        return {
            "data": NewsPostSchema(many=True).dump(news.items),
            "next_page": news.next_num,
            "prev_page": news.prev_num,
            "total": news.total,
        }


api.add_resource(News, "/news")
