# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-24 07:29:27
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 22:49:31
import contextlib
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import create_comment, permissions_required
from Onani.controllers.database.posts import parse_tags
from Onani.models import PostSchema
import Onani.models
from Onani.routes.api.v1._utils import str_to_rating

from . import api, csrf, db, limiter


class Posts(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument(
            "page", location="args", type=int, required=False, default=1
        )

        parser.add_argument(
            "per_page",
            location="args",
            type=int,
            required=False,
            default=current_app.config["API_PER_PAGE_POSTS"],
        )

        parser.add_argument("tags", location="args", type=str, required=False)

        # parser.add_argument(
        #     "id", location="args", type=int, default=None, required=False
        # )

        # Parse request args
        args = parser.parse_args()

        # Multiple posts
        posts = Onani.models.Post.query.order_by(Onani.models.Post.id.desc()).paginate(
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
        post = Onani.models.Post.query.filter_by(id=args["post_id"]).first_or_404()

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


class Post(Resource):
    def get(self):
        parser = reqparse.RequestParser()

        parser.add_argument(
            "id", location="args", type=int, default=None, required=True
        )

        # Parse request args
        args = parser.parse_args()

        post = Onani.models.Post.query.filter_by(id=args["id"]).first_or_404()
        return PostSchema().dump(post)

    def put(self):
        parser = reqparse.RequestParser()

        parser.add_argument(
            "id", location="args", type=int, default=None, required=True
        )

        parser.add_argument(
            "old_tags", location="args", type=str, default=None, required=False
        )

        parser.add_argument(
            "tags", location="args", type=str, default=None, required=False
        )

        parser.add_argument(
            "rating",
            location="args",
            type=str,
            default=None,
            required=False,
            choices=("s", "q", "e"),
            case_sensitive=False,
            trim=True,
        )

        parser.add_argument(
            "source", location="args", type=str, default=None, required=False, trim=True
        )

        parser.add_argument(
            "description",
            location="args",
            type=str,
            default=None,
            required=False,
            trim=True,
        )

        # Parse request args
        args = parser.parse_args()

        post: Onani.models.Post = Onani.models.Post.query.filter_by(
            id=args["id"]
        ).first_or_404()

        if args["rating"] is not None:
            post.rating = str_to_rating(args["rating"])

        if args["source"] is not None:
            post.source = args["source"]

        if args["description"] is not None:
            post.description = args["description"]

        # We put tag handling at the end so meta tags will take priority
        if args["tags"] is not None:
            tags = set(args["tags"].split(" "))
            if args["old_tags"] is not None:
                # If old_tags is set, we can use a differential approach to avoid race conditions
                # in case someone else edited the posts while another one was editing it
                old_tags = set(args["old_tags"].split(" "))

                added_tags = tags.difference(
                    old_tags
                )  # Tags in "tags" but not in "old_tags"
                removed_tags = old_tags.difference(
                    tags
                )  # Tags in "old_tags" but not in "tags"
                # tags that are in both are ignored as they were not edited

                # meta tags in removed_tags shouldn't be applied, but we need to parse so it can't really be avoided
                removed_tags = parse_tags(post, removed_tags)
                # added_tags might contain meta tags, so we parse for those
                added_tags = parse_tags(post, added_tags)

                post.tags.extend(added_tags)
                # it'd be easier to remove if post.tags was a set but whatever
                for t in removed_tags:
                    with contextlib.suppress(ValueError):
                        post.tags.remove(t)

            else:
                # we don't have old_tags, we just replace tags blindly
                post.tags = parse_tags(post, tags)

        db.session.commit()
        return PostSchema().dump(post)

    def patch(self):
        return self.put()


api.add_resource(Posts, "/posts")
api.add_resource(PostVote, "/posts/vote")
# api.add_resource(Post, "/post/<id>")
api.add_resource(Post, "/post")
