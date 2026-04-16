# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-15 04:57:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 15:53:28

from flask import current_app, abort
from flask_login import current_user
from flask_restful import Resource, reqparse
from Onani.models import Tag, TagSchema, TagType, UserRoles
from sqlalchemy import asc, desc

from . import api, db

_SORT_COLUMNS = {
    "id": Tag.id,
    "name": Tag.name,
    "type": Tag.type,
    "post_count": Tag.post_count,
}


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
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        # Single tag
        if args["id"]:
            tag = Tag.query.filter_by(id=args["id"]).first_or_404()
            return TagSchema().dump(tag)

        query = Tag.query
        if args["sort"]:
            col = _SORT_COLUMNS[args["sort"]]
            order_fn = asc if args["order"] == "asc" else desc
            query = query.order_by(order_fn(col))

        tags = query.paginate(per_page=args["per_page"], page=args["page"], error_out=False)

        return {
            "data": TagSchema(many=True, exclude=("posts",)).dump(
                sorted(tags.items, key=lambda t: (t.type.name, t.name))
            ),
            "next_page": tags.next_num,
            "prev_page": tags.prev_num,
            "total": tags.total,
        }

    def put(self):
        if not current_user.is_authenticated or not current_user.has_role(UserRoles.MODERATOR):
            abort(403)

        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        parser.add_argument("name", location="json", type=str, required=False)
        parser.add_argument(
            "type", location="json", type=str, required=False,
            choices=("general", "artist", "character", "copyright", "meta", "banned"),
        )
        args = parser.parse_args()

        tag = Tag.query.filter_by(id=args["id"]).first_or_404()

        if args["name"] is not None:
            name = args["name"].strip().lower().replace(" ", "_")
            existing = Tag.query.filter(Tag.name == name, Tag.id != args["id"]).first()
            if existing:
                return {"message": "Tag name already exists."}, 409
            tag.name = name

        if args["type"] is not None:
            tag.type = TagType[args["type"].upper()]

        db.session.commit()
        return TagSchema().dump(tag)


class TagsAutocomplete(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument("query", location="args", type=str, required=True)

        args = parser.parse_args()

        tags = (
            Tag.query.filter(Tag.name.ilike(f"{args['query'][:32].replace(' ', '_')}%"))
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
