# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-01 02:10:13
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 08:54:41
from flask import current_app
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from onani.controllers import permissions_required
from onani.services.posts import create_comment
from onani.models import Post, PostComment, PostCommentSchema, UserPermissions
from onani.models.post.comment import comment_upvotes

from . import api, db, limiter


def min_max_length(min_length, max_length):
    def validate(s):
        if len(s) >= min_length and len(s) <= max_length:
            return s
        raise ValueError(
            f"String must be at least {min_length} characters long and not over {max_length} characters."
        )

    return validate


class Comments(Resource):

    decorators = [limiter.limit("5/minute", methods=["POST"])]

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
        parser.add_argument("parent_id", type=int, location="json", required=False)

        # Parse request args
        args = parser.parse_args()

        # Look for post in db, if not found raise 404
        post: Post = Post.query.filter_by(id=args["post_id"]).first_or_404()

        parent = None
        if args.get("parent_id") is not None:
            parent = PostComment.query.filter_by(id=args["parent_id"]).first_or_404()
            if parent.post_id != post.id:
                return {"message": "Parent comment belongs to a different post."}, 400

        # Create the comment
        comment: PostComment = create_comment(current_user, post, args["content"], parent=parent)
        comment.has_upvoted = False

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

        parser.add_argument(
            "per_page",
            location="args",
            type=int,
            required=False,
            default=current_app.config["API_PER_PAGE_COMMENTS"],
        )

        # Parse request args
        args = parser.parse_args()
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        # Get the comments from the post id
        post: Post = Post.query.filter_by(id=args["post_id"]).first_or_404()

        comments = post.comments.order_by(PostComment.id.desc()).paginate(
            per_page=args["per_page"],
            page=args["page"],
            error_out=False,
        )

        items = comments.items
        if current_user.is_authenticated:
            comment_ids = [comment.id for comment in items]
            upvoted_comment_ids = set()
            if comment_ids:
                upvoted_comment_ids = {
                    comment_id
                    for (comment_id,) in db.session.query(comment_upvotes.c.comment_id)
                    .filter(
                        comment_upvotes.c.user_id == current_user.id,
                        comment_upvotes.c.comment_id.in_(comment_ids),
                    )
                    .all()
                }
            for comment in items:
                comment.has_upvoted = comment.id in upvoted_comment_ids
        else:
            for comment in items:
                comment.has_upvoted = False

        # Return the posts comments
        return {
            "data": PostCommentSchema(many=True).dump(items),
            "next": comments.next_num,
            "prev": comments.prev_num,
            "total": comments.total,
        }

    @login_required
    @permissions_required(UserPermissions.DELETE_COMMENTS)
    def delete(self):
        """Delete a comment. Requires UserPermissions.DELETE_COMMENTS"""
        parser = reqparse.RequestParser()
        parser.add_argument("comment_id", type=int, location="json", required=True)
        args = parser.parse_args()

        comment: PostComment = PostComment.query.filter_by(id=args["comment_id"]).first_or_404()
        db.session.delete(comment)
        db.session.commit()
        return {"message": "Comment deleted."}

    def put(self):
        """Not implemented, will be for editing comments"""
        pass


class CommentUpvote(Resource):
    decorators = [login_required, permissions_required(UserPermissions.CREATE_COMMENTS)]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("comment_id", type=int, location="json", required=True)
        args = parser.parse_args()

        comment: PostComment = PostComment.query.filter_by(id=args["comment_id"]).first_or_404()

        delete_result = db.session.execute(
            comment_upvotes.delete().where(
                comment_upvotes.c.comment_id == comment.id,
                comment_upvotes.c.user_id == current_user.id,
            )
        )

        has_upvoted = False
        if delete_result.rowcount == 0:
            try:
                db.session.execute(
                    comment_upvotes.insert().values(
                        comment_id=comment.id,
                        user_id=current_user.id,
                    )
                )
                has_upvoted = True
            except IntegrityError:
                # Another concurrent request inserted first; treat as upvoted.
                db.session.rollback()
                comment = PostComment.query.filter_by(id=args["comment_id"]).first_or_404()
                has_upvoted = True

        upvote_count = (
            db.session.query(func.count(comment_upvotes.c.user_id))
            .filter(comment_upvotes.c.comment_id == comment.id)
            .scalar()
            or 0
        )
        comment.upvote_count = upvote_count

        db.session.commit()
        return {
            "comment_id": comment.id,
            "upvote_count": upvote_count,
            "has_upvoted": has_upvoted,
        }


api.add_resource(Comments, "/comments")
api.add_resource(CommentUpvote, "/comments/upvote")
