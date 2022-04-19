# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-01 02:10:13
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 12:40:07

from flask import abort, jsonify, request
from flask_login import current_user, login_required
from Onani.controllers import create_comment
from Onani.models import Post, PostComment, PostCommentSchema

from . import admin_api, csrf, db, main_api, make_api_response


@main_api.route("/comments/post", methods=["POST"])
@login_required
@csrf.exempt
def comment_post():
    if data := request.get_json():
        post = Post.query.filter_by(id=data["post_id"]).first_or_404()
        comment = create_comment(current_user, post, data["content"])
        return make_api_response(PostCommentSchema().dump(comment))
    abort(400)


@main_api.route("/comments/", methods=["GET"])
@csrf.exempt
def get_comments():
    if post_id := request.args.get("post_id"):
        post: Post = Post.query.filter_by(id=post_id).first_or_404()
        return make_api_response(
            {
                "data": PostCommentSchema(many=True).dump(
                    post.comments.order_by(PostComment.id.desc())
                )
            }
        )
    abort(400)
