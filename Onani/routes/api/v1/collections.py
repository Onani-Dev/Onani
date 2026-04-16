# -*- coding: utf-8 -*-
"""Collections API for the Vue SPA."""
from flask import abort, current_app
from flask_login import current_user
from flask_restful import Resource, reqparse
from Onani.models import Collection, CollectionStatus, Post, UserRoles
from Onani.models.schemas.collection import CollectionSchema
from Onani.models.schemas.post import PostSchema

from . import api, db


def _can_manage(collection: Collection) -> bool:
    return current_user.is_authenticated and (
        collection.creator == current_user.id
        or current_user.has_role(UserRoles.MODERATOR)
    )


class Collections(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, required=False, default=1)
        parser.add_argument("per_page", location="args", type=int, required=False,
            default=current_app.config.get("PER_PAGE_COLLECTIONS", 80))
        parser.add_argument("id", location="args", type=int, default=None)

        args = parser.parse_args()
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        if args["id"]:
            collection = Collection.query.filter_by(id=args["id"]).first_or_404()
            return CollectionSchema().dump(collection)

        collections = Collection.query.paginate(
            per_page=args["per_page"], page=args["page"], error_out=False
        )
        return {
            "data": CollectionSchema(many=True, exclude=("posts",)).dump(collections.items),
            "next_page": collections.next_num,
            "prev_page": collections.prev_num,
            "total": collections.total,
        }

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("title", location="json", type=str, required=True)
        parser.add_argument("description", location="json", type=str, default="")
        args = parser.parse_args()

        collection = Collection(
            title=args["title"].strip(),
            description=args["description"],
            creator=current_user.id,
            status=CollectionStatus.ACCEPTED,
        )
        db.session.add(collection)
        db.session.commit()
        return CollectionSchema(exclude=("posts",)).dump(collection), 201

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        parser.add_argument("title", location="json", type=str, required=False)
        parser.add_argument("description", location="json", type=str, required=False)
        args = parser.parse_args()

        collection = Collection.query.filter_by(id=args["id"]).first_or_404()
        if not _can_manage(collection):
            abort(403)

        if args["title"] is not None:
            collection.title = args["title"].strip()
        if args["description"] is not None:
            collection.description = args["description"]

        db.session.commit()
        return CollectionSchema(exclude=("posts",)).dump(collection)

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        args = parser.parse_args()

        collection = Collection.query.filter_by(id=args["id"]).first_or_404()
        if not _can_manage(collection):
            abort(403)

        db.session.delete(collection)
        db.session.commit()
        return {}, 204


class CollectionPosts(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("collection_id", location="json", type=int, required=True)
        parser.add_argument("post_id", location="json", type=int, required=True)
        args = parser.parse_args()

        collection = Collection.query.filter_by(id=args["collection_id"]).first_or_404()
        if not _can_manage(collection):
            abort(403)

        post = Post.query.filter_by(id=args["post_id"]).first_or_404()
        if not collection.posts.filter_by(id=post.id).first():
            collection.posts.append(post)
            db.session.commit()
        return CollectionSchema().dump(collection)

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument("collection_id", location="json", type=int, required=True)
        parser.add_argument("post_id", location="json", type=int, required=True)
        args = parser.parse_args()

        collection = Collection.query.filter_by(id=args["collection_id"]).first_or_404()
        if not _can_manage(collection):
            abort(403)

        post = collection.posts.filter_by(id=args["post_id"]).first()
        if post:
            collection.posts.remove(post)
            db.session.commit()
        return CollectionSchema().dump(collection)


api.add_resource(Collections, "/collections")
api.add_resource(CollectionPosts, "/collections/posts")
