# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-16 00:55:57
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 21:37:05
from flask import abort, request
from flask_login import login_required
from Onani.models import Tag, TagSchema
from sqlalchemy import text

from . import main_api, make_api_response


@main_api.route("/tags", methods=["GET"])
# @login_required
def get_tags():
    page = request.args.get("page", "0")
    per_page = request.args.get("per_page", "25")

    page = int(page) if page.isdigit() else 0
    per_page = int(per_page) if per_page.isdigit() else 25

    sort_order = "desc"
    order_by = []

    if order := request.args.get("order"):
        if order.lower() not in ["asc", "desc"]:
            abort(400)
        sort_order = order

    if sort := request.args.get("sort"):
        sort = set(sort.lower().split(","))
        for s in sort:
            if s not in ["id", "name", "type", "post_count"]:
                abort(400)
            order_by.append(f"tags_{s} {sort_order}")

    order_by = ", ".join(order_by) if order_by else ""

    tags = Tag.query.order_by(text(order_by)).paginate(
        per_page=per_page, page=page, error_out=False
    )

    return make_api_response(
        {
            "data": TagSchema(many=True, exclude=("posts",)).dump(
                sorted(tags.items, key=lambda t: (t.type.name, t.name))
            ),
            "next_page": tags.next_num,
            "prev_page": tags.prev_num,
            "total": tags.total,
        }
    )
