# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-24 07:29:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-26 16:22:02
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import create_comment, permissions_required
from Onani.models import Post, PostSchema

from . import api, csrf, db, limiter


class Posts(Resource):
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
            default=current_app.config["API_PER_PAGE_POSTS"],
        )

        parser.add_argument("tags", location="args", type=str, required=False)

        parser.add_argument(
            "id", location="args", type=int, default=None, required=False
        )

        # Parse request args
        args = parser.parse_args()

        # Single post
        if args["id"]:
            post = Post.query.filter_by(id=args["id"]).first_or_404()
            return PostSchema().dump(post)

        # Multiple posts
        posts = Post.query.order_by(Post.id.desc()).paginate(
            per_page=args["per_page"], page=args["page"], error_out=False
        )
        return {
            "data": PostSchema(many=True).dump(posts.items),
            "next_page": posts.next_num,
            "prev_page": posts.prev_num,
            "total": posts.total,
        }


class PostVote(Resource):
    decorators = [login_required]

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument("post_id", location="json", type=int, required=True)

        parser.add_argument(
            "type",
            location="json",
            type=str,
            required=True,
            choices=("upvote", "downvote"),
        )

        # Parse request args
        args = parser.parse_args()

        # Get the post from database
        post = Post.query.filter_by(id=args["post_id"]).first_or_404()

        # Check type of vote
        match args["type"]:
            # Upvoting
            case "upvote":
                # Remove a downvote if there is one.
                if post.downvoters.filter_by(id=current_user.id).first():
                    post.downvoters.remove(current_user)

                # toggle between off and on
                if not post.upvoters.filter_by(id=current_user.id).first():
                    # toggle on
                    post.upvoters.append(current_user)
                else:
                    # toggle off
                    post.upvoters.remove(current_user)
            # Downvoting
            case "downvote":
                # remove an upvote if there is one
                if post.upvoters.filter_by(id=current_user.id).first():
                    post.upvoters.remove(current_user)

                # toggle between off and on
                if not post.downvoters.filter_by(id=current_user.id).first():
                    # toggle on
                    post.downvoters.append(current_user)
                else:
                    # toggle off
                    post.downvoters.remove(current_user)

        # commit to database
        db.session.commit()

        return {
            "score": post.score,
            "has_upvoted": current_user.has_upvoted(post),
            "has_downvoted": current_user.has_downvoted(post),
        }


api.add_resource(Posts, "/posts")
api.add_resource(PostVote, "/posts/vote")
