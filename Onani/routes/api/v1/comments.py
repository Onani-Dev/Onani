# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-01 02:10:13
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 12:18:02
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import create_comment, permissions_required
from Onani.models import Post, PostComment, PostCommentSchema
from Onani.models.user.permissions import UserPermissions

from . import api


def min_max_length(min_length, max_length):
    def validate(s):
        if len(s) >= min_length and len(s) <= max_length:
            return s
        raise ValueError(
            f"String must be at least {min_length} characters long and not over {max_length} characters."
        )

    return validate


class Comments(Resource):

    # decorators = [login_required]

    @login_required
    @permissions_required(UserPermissions.CREATE_COMMENTS)
    def post(self):
        """Create a comment on a post. Requires UserPermissions.CREATE_COMMENTS"""

        # Init parser
        parser = reqparse.RequestParser()

        # require post id
        parser.add_argument("post_id", type=int, location="json", required=True)

        # and content
        parser.add_argument(
            "content", type=min_max_length(1, 2000), location="json", required=True
        )

        # Parse request args
        args = parser.parse_args()

        # Look for post in db, if not found raise 404
        post: Post = Post.query.filter_by(id=args["post_id"]).first_or_404()
        # Create the comment
        comment: PostComment = create_comment(current_user, post, args["content"])

        # return comment dumped as json
        return PostCommentSchema().dump(comment)

    def get(self):
        """Get the comments from a post."""
        # Init parser
        parser = reqparse.RequestParser()

        # require post id
        parser.add_argument("post_id", location="args", type=int, required=True)
        parser.add_argument(
            "page", location="args", type=int, required=False, nullable=False
        )

        # Parse request args
        args = parser.parse_args()

        # Get the comments from the post id
        post: Post = Post.query.filter_by(id=args["post_id"]).first_or_404()

        comments = post.comments.order_by(PostComment.id.desc()).paginate(
            per_page=current_app.config["API_PER_PAGE_COMMENTS"],
            page=args["page"],
            error_out=False,
        )

        # Return the posts comments
        return {
            "data": PostCommentSchema(many=True).dump(comments.items),
            "next": comments.next_num,
            "prev": comments.prev_num,
            "total": comments.total,
        }

    def delete(self):
        """Not implemented, will be for deleting comments"""
        pass

    def put(self):
        """Not implemented, will be for editing comments"""
        pass


api.add_resource(Comments, "/comments")
