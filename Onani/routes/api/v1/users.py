# -*- coding: utf-8 -*-
"""Users API — list and retrieve user profiles for the Vue SPA."""
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.models import Post, User, UserSchema
from Onani.models.schemas.post import PostSchema

from . import api, db


class Users(Resource):
    decorators = [login_required]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, required=False, default=1)
        parser.add_argument("per_page", location="args", type=int, required=False,
            default=current_app.config.get("PER_PAGE_USERS", 30))
        parser.add_argument("id", location="args", type=int, default=None)

        args = parser.parse_args()
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        if args["id"]:
            user = User.query.filter_by(id=args["id"]).first_or_404()
            return UserSchema().dump(user)

        users = User.query.order_by(User.post_count.desc()).paginate(
            per_page=args["per_page"], page=args["page"], error_out=False
        )
        return {
            "data": UserSchema(many=True).dump(users.items),
            "next_page": users.next_num,
            "prev_page": users.prev_num,
            "total": users.total,
        }


class UserPosts(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("user_id", location="args", type=int, required=True)
        parser.add_argument("page", location="args", type=int, required=False, default=1)
        parser.add_argument("per_page", location="args", type=int, required=False,
            default=current_app.config.get("PER_PAGE_USER_POSTS", 50))

        args = parser.parse_args()
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        user = User.query.filter_by(id=args["user_id"]).first_or_404()
        posts = user.posts.order_by(Post.id.desc()).paginate(
            per_page=args["per_page"], page=args["page"], error_out=False
        )
        return {
            "data": PostSchema(many=True).dump(posts.items),
            "next_page": posts.next_num,
            "prev_page": posts.prev_num,
            "total": posts.total,
        }


api.add_resource(Users, "/users")
api.add_resource(UserPosts, "/users/posts")
