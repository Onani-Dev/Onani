# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:26:01
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-16 01:34:08

from flask import request
from flask_login import login_required
from Onani.models import Post, PostSchema

from . import main_api, make_api_response


@main_api.route("/posts", methods=["GET"])
@login_required
def get_posts():
    page = request.args.get("page", "0")
    per_page = request.args.get("per_page", "10")

    page = int(page) if page.isdigit() else 0
    per_page = int(per_page) if per_page.isdigit() else 10

    posts = Post.query.paginate(per_page=per_page, page=page, error_out=False)

    post_schema = PostSchema(many=True)
    return make_api_response(
        {
            "data": post_schema.dump(posts.items),
            "next_page": posts.next_num,
            "prev_page": posts.prev_num,
            "total": posts.total,
        }
    )
