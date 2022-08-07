# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-07 09:47:07
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-07 09:56:46


from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import permissions_required
from Onani.models import UserPermissions, NewsPost, NewsPostSchema

from . import api


class NewsAdmin(Resource):
    decorators = [login_required, permissions_required(UserPermissions.CREATE_NEWS)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", location="json", type=str, required=True)
        parser.add_argument("content", location="json", type=str, required=True)

        data = parser.parse_args()

        article = NewsPost(
            author=current_user,
            title=data["title"],
            content=data["content"],
        )

        article.save_to_db()

        return NewsPostSchema().dump(article)


api.add_resource(NewsAdmin, "/admin/news")
