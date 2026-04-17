# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-24 07:29:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-01 14:12:39
from flask import current_app, abort, request
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from Onani.controllers import permissions_required
from Onani.services.posts import create_comment, set_tags, upload_post
from Onani.services.queries import query_posts
from Onani.services.hot import get_hot_posts, record_view
from Onani.models import Post as _Post
from Onani.models import PostRating, PostSchema, UserPermissions
from Onani.models import Tag, TagSchema
from Onani.models.post._post import post_upvotes, post_downvotes
from sqlalchemy import func
from PIL import UnidentifiedImageError

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
        args["per_page"] = min(args["per_page"], current_app.config["API_MAX_PER_PAGE"])

        # Build the base query - filter by tags when provided
        if args["tags"]:
            raw_tags = [t for t in args["tags"].split() if t]
            include_tags = [t for t in raw_tags if not t.startswith("-")]
            exclude_tags = [t.lstrip("-") for t in raw_tags if t.startswith("-") and len(t) > 1]
            posts = query_posts(tags=include_tags or None, exclude_tags=exclude_tags or None).paginate(
                per_page=args["per_page"], page=args["page"], error_out=False
            )
        else:
            posts = _Post.query.order_by(_Post.id.desc()).paginate(
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
        post = _Post.query.filter_by(id=args["post_id"]).first_or_404()

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

        post = _Post.query.filter_by(id=args["id"]).first_or_404()

        # Record a view event for the hot-posts algorithm; log but don't
        # fail the request if this step encounters an error.
        try:
            record_view(post.id)
        except Exception:
            current_app.logger.debug(
                "Failed to record view for post %s", post.id, exc_info=True
            )

        dump = PostSchema().dump(post)
        dump["has_upvoted"] = current_user.is_authenticated and current_user.has_upvoted(post)
        dump["has_downvoted"] = current_user.is_authenticated and current_user.has_downvoted(post)
        return dump

    def put(self):
        if not current_user.is_authenticated:
            abort(401)

        parser = reqparse.RequestParser()

        parser.add_argument(
            "id", location="json", type=int, default=None, required=True
        )

        parser.add_argument(
            "old_tags", location="json", type=str, default=None, required=False
        )

        parser.add_argument(
            "tags", location="json", type=str, default=None, required=False
        )

        parser.add_argument(
            "rating",
            location="json",
            type=str,
            default=None,
            required=False,
            choices=("s", "q", "e"),
            case_sensitive=False,
            trim=True,
        )

        parser.add_argument(
            "source", location="json", type=str, default=None, required=False, trim=True
        )

        parser.add_argument(
            "description",
            location="json",
            type=str,
            default=None,
            required=False,
            trim=True,
        )

        # Parse request args
        args = parser.parse_args()

        post: _Post = _Post.query.filter_by(id=args["id"]).first_or_404()

        if not current_user.can_edit_post(post):
            abort(403)

        if args["rating"] is not None:
            post.rating = PostRating(
                args["rating"]
            )  # It's already lowercase and stripped

        if args["source"] is not None:
            post.source = args["source"]

        if args["description"] is not None:
            post.description = args["description"]

        # We put tag handling at the end so meta tags will take priority
        if args["tags"] is not None:
            tags = set(args["tags"].split(" "))
            old_tags = set(args["old_tags"].split(" ")) if args["old_tags"] is not None else set()
            can_create = current_user.has_permissions(UserPermissions.CREATE_TAGS)
            set_tags(
                post,
                tags,
                old_tags,
                can_create_tags=can_create,
                tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                post_min_tags=current_app.config["POST_MIN_TAGS"],
            )

        db.session.commit()
        return PostSchema().dump(post)

    def patch(self):
        return self.put()


class PostUpload(Resource):
    """Multipart file upload endpoint for the Vue SPA."""

    decorators = [login_required, limiter.limit("10/minute")]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("tags", location="form", type=str, required=True)
        parser.add_argument("source", location="form", type=str, default="", required=False)
        parser.add_argument("description", location="form", type=str, default="", required=False)
        parser.add_argument("rating", location="form", type=str, required=True,
            choices=("s", "q", "e"), case_sensitive=False)
        args = parser.parse_args()

        if "file" not in request.files or not request.files["file"].filename:
            abort(400, description="No file provided.")

        file = request.files["file"]
        file_data = file.stream.read()

        can_create = current_user.has_permissions(UserPermissions.CREATE_TAGS)

        try:
            post = upload_post(
                file_data=file_data,
                original_filename=file.filename,
                tags_raw=args["tags"],
                source=args["source"],
                description=args["description"],
                uploader=current_user,
                rating=args["rating"],
                images_dir=current_app.config["IMAGES_DIR"],
                can_create_tags=can_create,
                tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                post_min_tags=current_app.config["POST_MIN_TAGS"],
            )
        except UnidentifiedImageError:
            abort(400, description="The file could not be read as an image.")
        except ValueError as e:
            abort(400, description=str(e))

        return PostSchema().dump(post), 201


class PostWater(Resource):
    decorators = [login_required]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("post_id", location="json", type=int, required=True)
        args = parser.parse_args()

        post = _Post.query.filter_by(id=args["post_id"]).first_or_404()
        post.water_count = (post.water_count or 0) + 1
        db.session.commit()

        return {"water_count": post.water_count}


class PostsHot(Resource):
    """Return posts ranked by the hot-score algorithm (cached 30 min)."""

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "limit",
            location="args",
            type=int,
            required=False,
            default=20,
        )
        args = parser.parse_args()
        limit = min(max(args["limit"], 1), 100)

        hot = get_hot_posts(limit=limit)
        return {
            "data": PostSchema(many=True).dump(hot),
            "total": len(hot),
        }


class PostsHome(Resource):
    def get(self):
        # Recent
        recent = _Post.query.order_by(_Post.id.desc()).limit(8).all()

        # Hot posts (scored by the hot algorithm, cached 30 min)
        hot = get_hot_posts(limit=8)

        # Popular by (upvotes - downvotes)
        ups = (
            db.session.query(post_upvotes.c.post_id, func.count().label("ups"))
            .group_by(post_upvotes.c.post_id)
            .subquery()
        )
        downs = (
            db.session.query(post_downvotes.c.post_id, func.count().label("downs"))
            .group_by(post_downvotes.c.post_id)
            .subquery()
        )
        popular = (
            _Post.query
            .outerjoin(ups, _Post.id == ups.c.post_id)
            .outerjoin(downs, _Post.id == downs.c.post_id)
            .order_by(
                (func.coalesce(ups.c.ups, 0) - func.coalesce(downs.c.downs, 0)).desc()
            )
            .limit(8)
            .all()
        )

        # Random single post
        random_post = _Post.query.order_by(func.random()).first()

        # Random tags with at least one post
        random_tags = (
            Tag.query
            .filter(Tag.post_count > 0)
            .order_by(func.random())
            .limit(20)
            .all()
        )

        schema = PostSchema(many=True)
        return {
            "recent": schema.dump(recent),
            "hot": schema.dump(hot),
            "popular": schema.dump(popular),
            "random": PostSchema().dump(random_post) if random_post else None,
            "tags": TagSchema(many=True, exclude=("posts",)).dump(random_tags),
        }


api.add_resource(PostsHome, "/posts/home")
api.add_resource(PostsHot, "/posts/hot")
api.add_resource(Posts, "/posts")
api.add_resource(PostVote, "/posts/vote")
api.add_resource(PostWater, "/posts/water")
api.add_resource(PostUpload, "/posts/upload")
api.add_resource(Post, "/post")
