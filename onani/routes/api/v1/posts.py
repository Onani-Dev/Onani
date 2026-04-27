# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-24 07:29:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-01 14:12:39
import contextlib
import random

from flask import current_app, abort, request
from flask_login import current_user, login_required
from flask_restful import Resource, reqparse
from onani.controllers import permissions_required
from onani.services.posts import create_comment, set_tags, upload_post
from onani.services.deepdanbooru import (
    DeepDanbooruUnavailableError,
    get_deepdanbooru_status,
    suggest_labels_for_bytes,
    suggest_labels_for_post,
)
from onani.services.queries import query_posts
from onani.models import Post as _Post
from onani.models import PostRating, PostSchema, UserPermissions
from onani.models import Tag, TagSchema
from onani.models.post._post import post_upvotes, post_downvotes, post_waters
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
            posts = _Post.query.filter(_Post.hidden.is_(False)).order_by(_Post.id.desc()).paginate(
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
        dump = PostSchema().dump(post)
        dump["has_upvoted"] = current_user.is_authenticated and current_user.has_upvoted(post)
        dump["has_downvoted"] = current_user.is_authenticated and current_user.has_downvoted(post)
        dump["has_favourited"] = current_user.is_authenticated and current_user.has_favourited(post)
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

    def delete(self):
        if not current_user.is_authenticated:
            abort(401)

        parser = reqparse.RequestParser()
        parser.add_argument("id", location="json", type=int, required=True)
        args = parser.parse_args()

        post = _Post.query.filter_by(id=args["id"]).first_or_404()

        can_hard_delete = current_user.has_permissions(UserPermissions.DELETE_POSTS)
        is_uploader = current_user.id == post.uploader_id

        if not (can_hard_delete or is_uploader):
            abort(403)

        db.session.delete(post)
        db.session.commit()
        return "", 204


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


class PostAutoTagsStatus(Resource):
    def get(self):
        return get_deepdanbooru_status(current_app.config)


class PostAutoTags(Resource):
    decorators = [login_required, limiter.limit("10/minute")]

    def post(self):
        has_file_upload = bool(request.files and request.files.get("file"))
        payload = request.get_json(silent=True) or {}

        threshold_raw = request.form.get("threshold") if has_file_upload else payload.get("threshold")
        threshold = float(threshold_raw) if threshold_raw is not None else None

        try:
            if has_file_upload:
                file_storage = request.files["file"]
                if not file_storage.filename:
                    abort(400, description="No file provided.")
                labels = suggest_labels_for_bytes(file_storage.read(), current_app.config, threshold=threshold)
            else:
                # If the client intended multipart but omitted the file, surface a clearer message.
                content_type = (request.content_type or "").lower()
                if "multipart/form-data" in content_type:
                    abort(400, description="No file provided.")

                post_id = payload.get("post_id")
                if post_id is None:
                    abort(400, description="Provide either multipart file or JSON post_id.")

                try:
                    post_id = int(post_id)
                except (TypeError, ValueError):
                    abort(400, description="post_id must be an integer.")

                post = _Post.query.filter_by(id=post_id).first_or_404()
                if not current_user.can_edit_post(post):
                    abort(403)

                labels = suggest_labels_for_post(post, current_app.config, threshold=threshold)
        except DeepDanbooruUnavailableError as exc:
            abort(503, description=str(exc))
        except ValueError as exc:
            abort(400, description=str(exc))

        suggestions = labels["tags"]

        if not current_user.has_permissions(UserPermissions.CREATE_TAGS):
            suggestions = [item for item in suggestions if item["exists"]]

        return {
            "available": True,
            "threshold": threshold if threshold is not None else current_app.config["DEEPDANBOORU_THRESHOLD"],
            "data": suggestions,
            "rating": labels.get("rating"),
            "rating_score": labels.get("rating_score"),
        }


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


class PostFavourite(Resource):
    decorators = [login_required]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("post_id", location="json", type=int, required=True)
        args = parser.parse_args()

        post = _Post.query.filter_by(id=args["post_id"]).first_or_404()

        if post.waterers.filter_by(id=current_user.id).first():
            post.waterers.remove(current_user)
            favourited = False
        else:
            post.waterers.append(current_user)
            favourited = True

        db.session.commit()
        return {"has_favourited": favourited}


class PostFavourites(Resource):
    decorators = [login_required]

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page", location="args", type=int, default=1)
        parser.add_argument("per_page", location="args", type=int, default=20)
        args = parser.parse_args()

        per_page = min(args["per_page"], 50)
        paginated = (
            _Post.query
            .join(post_waters, _Post.id == post_waters.c.post_id)
            .filter(post_waters.c.user_id == current_user.id)
            .order_by(_Post.id.desc())
            .paginate(page=args["page"], per_page=per_page, error_out=False)
        )

        return {
            "data": PostSchema(many=True).dump(paginated.items),
            "page": args["page"],
            "next_page": args["page"] + 1 if paginated.has_next else None,
            "prev_page": args["page"] - 1 if paginated.has_prev else None,
            "total": paginated.total,
        }


class PostsHome(Resource):
    def get(self):
        # Recent
        recent = _Post.query.order_by(_Post.id.desc()).limit(8).all()

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

        # Random single post — use a random offset to avoid full-table ORDER BY random()
        post_count = _Post.query.count()
        random_post = (
            _Post.query.offset(random.randint(0, post_count - 1)).first()
            if post_count
            else None
        )

        # Random tags with at least one post
        tag_q = Tag.query.filter(Tag.post_count > 0)
        tag_count = tag_q.count()
        if tag_count > 20:
            random_tags = tag_q.offset(random.randint(0, tag_count - 20)).limit(20).all()
        else:
            random_tags = tag_q.all()

        schema = PostSchema(many=True)
        return {
            "recent": schema.dump(recent),
            "popular": schema.dump(popular),
            "random": PostSchema().dump(random_post) if random_post else None,
            "tags": TagSchema(many=True, exclude=("posts",)).dump(random_tags),
        }


api.add_resource(PostsHome, "/posts/home")
api.add_resource(Posts, "/posts")
api.add_resource(PostVote, "/posts/vote")
api.add_resource(PostWater, "/posts/water")
api.add_resource(PostFavourite, "/posts/favourite")
api.add_resource(PostFavourites, "/posts/favourites")
api.add_resource(PostUpload, "/posts/upload")
api.add_resource(PostAutoTagsStatus, "/posts/auto-tags/status")
api.add_resource(PostAutoTags, "/posts/auto-tags")
api.add_resource(Post, "/post")
