# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-07 09:47:07
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-08 08:59:45


from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from onani.controllers import permissions_required
from onani.services.news import create_news
from onani.models import NewsPost, NewsPostSchema, NewsType, UserPermissions

from . import api


class NewsAdmin(Resource):
    decorators = [login_required, permissions_required(UserPermissions.CREATE_NEWS)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", location="json", type=str, required=True)
        parser.add_argument("content", location="json", type=str, required=True)
        parser.add_argument(
            "type",
            location="json",
            type=int,
            default=NewsType.ANNOUNCEMENT.value,
            choices=(x[0].value for x in NewsType.choices()),
        )

        data = parser.parse_args()

        article = create_news(
            title=data["title"],
            content=data["content"],
            type=NewsType(data["type"]),
            author=current_user,
        )

        return NewsPostSchema().dump(article)


api.add_resource(NewsAdmin, "/admin/news")
