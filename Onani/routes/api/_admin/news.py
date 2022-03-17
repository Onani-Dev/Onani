# -*- coding: utf-8 -*-
# @Author: dirt3009
# @Date:   2022-03-17 20:38:10
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-03-17 23:23:31

import datetime

from flask import jsonify, request
from flask_login import current_user
from Onani.controllers import role_required
from Onani.models import UserRoles, NewsPost, NewsPostSchema

from . import admin_api, db
from .. import make_api_response


@admin_api.route("/news", methods=["POST", "DELETE"])
@role_required(role=UserRoles.ADMIN)
def create_article():
    if request.method == "POST":
        data = request.json
        article = NewsPost(
            author=current_user.id,
            title=data["title"],
            content=data["content"],
        )
        article.save_to_db()
        return make_api_response()
    elif request.method == "DELETE":
        return make_api_response(error="Not implemented yet.", code=501) # why does this not work properly when i add code=501 part?
