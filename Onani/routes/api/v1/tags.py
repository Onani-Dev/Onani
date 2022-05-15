# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-15 04:57:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 15:53:28

from email.policy import default
from flask import current_app
from flask_restful import Resource, reqparse
from Onani.models import Tag, TagSchema
from sqlalchemy import text

from . import api


class Tags(Resource):
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
            default=current_app.config["API_PER_PAGE_TAGS"],
        )

        parser.add_argument(
            "order", choices=("asc", "desc"), location="args", type=str, default="desc"
        )

        parser.add_argument(
            "sort",
            choices=("id", "name", "type", "post_count"),
            location="args",
            type=str,
        )

        parser.add_argument("id", location="args", type=int, default=None)

        # Parse request args
        args = parser.parse_args()

        # Single tag
        if args["id"]:
            tag = Tag.query.filter_by(id=args["id"]).first_or_404()
            return TagSchema().dump(tag)

        tags = Tag.query.order_by(
            text(f"tags_{args['sort']} {args['order']}" if args["sort"] else "")
        ).paginate(per_page=args["per_page"], page=args["page"], error_out=False)

        return {
            "data": TagSchema(many=True, exclude=("posts",)).dump(
                sorted(tags.items, key=lambda t: (t.type.name, t.name))
            ),
            "next_page": tags.next_num,
            "prev_page": tags.prev_num,
            "total": tags.total,
        }


class TagsAutocomplete(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument("query", location="args", type=str, required=True)

        args = parser.parse_args()

        tags = (
            Tag.query.filter(Tag.name.like(f"{args['query'][:32].replace(' ', '_')}%"))
            .order_by(Tag.post_count.desc())
            .limit(current_app.config["API_AUTOCOMPLETE_LIMIT"])
        )
        return {
            "data": TagSchema(many=True, exclude=("posts",)).dump(
                sorted(tags, key=lambda t: (t.type.name, t.name))
            )
        }


api.add_resource(Tags, "/tags")
api.add_resource(TagsAutocomplete, "/tags/autocomplete")
