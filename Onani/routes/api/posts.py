# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 18:26:01
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-24 01:26:47

from flask import request, abort
from flask_login import current_user, login_required
from Onani.models import Post, PostSchema, User


from . import csrf, db, main_api, make_api_response


@main_api.route("/posts", methods=["GET"])
@login_required
def get_posts():
    page = request.args.get("page", "0")
    per_page = request.args.get("per_page", "10")

    page = int(page) if page.isdigit() else 0
    per_page = int(per_page) if per_page.isdigit() else 10

    posts = Post.query.paginate(per_page=per_page, page=page, error_out=False)

    post_schema = PostSchema(many=True)
    return make_api_response(
        {
            "data": post_schema.dump(posts.items),
            "next_page": posts.next_num,
            "prev_page": posts.prev_num,
            "total": posts.total,
        }
    )


@main_api.route("/posts/upvote", methods=["POST"])
@login_required
@csrf.exempt
def post_upvote():
    data = request.get_json()

    post_id = data.get("post_id")

    if not post_id or not str(post_id).isdigit():
        abort(400)

    post = Post.query.filter_by(id=post_id).first_or_404()

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

    # commit to database
    db.session.commit()

    return make_api_response(
        {
            "score": post.score,
            "has_upvoted": current_user.has_upvoted(post),
            "has_downvoted": current_user.has_downvoted(post),
        }
    )


@main_api.route("/posts/downvote", methods=["POST"])
@csrf.exempt
@login_required
def post_downvote():
    data = request.get_json()

    post_id = data.get("post_id")

    if not post_id or not str(post_id).isdigit():
        abort(400)

    post = Post.query.filter_by(id=post_id).first_or_404()

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

    return make_api_response(
        {
            "score": post.score,
            "has_downvoted": current_user.has_downvoted(post),
            "has_upvoted": current_user.has_upvoted(post),
        }
    )
