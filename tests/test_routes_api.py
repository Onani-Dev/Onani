# -*- coding: utf-8 -*-
"""Tests for the REST API v1 endpoints."""
import json
import os
from types import SimpleNamespace

import pytest
from PIL import Image


class TestAPIIndex:
    def test_api_index(self, client):
        resp = client.get("/api/v1/")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "version" in data


class TestMediaRoutes:
    def test_image_thumbnail_generated_by_flask(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="abcdef1234567890", filename="abcdef1234567890.png")
            filename = post.filename

        src = os.path.join(app.config["IMAGES_DIR"], "ab", filename)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        Image.new("RGB", (1600, 900), color=(120, 60, 40)).save(src, format="PNG")

        resp = client.get(f"/images/thumbnail/ab/{filename}?size=small")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/")

        cached = os.path.join(
            app.config["IMAGES_DIR"],
            ".thumbs",
            "images",
            "150x150",
            "ab",
            "abcdef1234567890.jpg",
        )
        assert os.path.isfile(cached)

    def test_avatar_thumbnail_generated_by_flask(self, client, make_user, app):
        with app.app_context():
            user = make_user(username="avatar_user")
            user.settings.avatar = "/avatars/avatar001.png"
            from onani import db
            db.session.commit()

        src = os.path.join(app.config["AVATARS_DIR"], "avatar001.png")
        os.makedirs(os.path.dirname(src), exist_ok=True)
        Image.new("RGB", (600, 600), color=(20, 100, 180)).save(src, format="PNG")

        resp = client.get("/avatars/thumbnail/avatar001.png?size=150")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/")

        cached = os.path.join(
            app.config["AVATARS_DIR"],
            ".thumbs",
            "avatars",
            "150x150",
            "av",
            "avatar001.jpg",
        )
        assert os.path.isfile(cached)

    def test_video_thumbnail_route_uses_videos_cache(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="cdef012345678901", filename="cdef012345678901.jpg")
            filename = post.filename

        src = os.path.join(app.config["IMAGES_DIR"], "cd", filename)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        Image.new("RGB", (640, 480), color=(80, 120, 160)).save(src, format="JPEG")

        resp = client.get(f"/videos/thumbnail/cd/{filename}?size=small")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/")

        cached = os.path.join(
            app.config["IMAGES_DIR"],
            ".thumbs",
            "videos",
            "150x150",
            "cd",
            "cdef012345678901.jpg",
        )
        assert os.path.isfile(cached)

    def test_image_thumbnail_does_not_write_to_videos_cache(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="defa123456789012", filename="defa123456789012.png")
            filename = post.filename

        src = os.path.join(app.config["IMAGES_DIR"], "de", filename)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        Image.new("RGB", (800, 600), color=(200, 100, 50)).save(src, format="PNG")

        client.get(f"/images/thumbnail/de/{filename}?size=small")

        videos_cached = os.path.join(
            app.config["IMAGES_DIR"],
            ".thumbs",
            "videos",
            "150x150",
            "de",
            "defa123456789012.jpg",
        )
        assert not os.path.isfile(videos_cached)

    def test_sample_route_generated_by_flask(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="bcfed01234567890", filename="bcfed01234567890.png")
            filename = post.filename

        src = os.path.join(app.config["IMAGES_DIR"], "bc", filename)
        os.makedirs(os.path.dirname(src), exist_ok=True)
        Image.new("RGB", (2400, 1400), color=(200, 40, 40)).save(src, format="PNG")

        resp = client.get(f"/sample/bc/{filename}")
        assert resp.status_code == 200
        assert resp.content_type.startswith("image/")

        cached = os.path.join(
            app.config["IMAGES_DIR"],
            ".thumbs",
            "sample",
            "800x2000",
            "bc",
            "bcfed01234567890.jpg",
        )
        assert os.path.isfile(cached)


class TestPostsAPI:
    def test_get_posts_empty(self, client):
        resp = client.get("/api/v1/posts")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_posts_returns_list(self, client, make_post, app):
        with app.app_context():
            make_post(sha256_hash="apihash1")
            make_post(sha256_hash="apihash2")

        resp = client.get("/api/v1/posts")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["data"]) >= 2

    def test_get_single_post(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="singleapihash")
            post_id = post.id

        resp = client.get(f"/api/v1/post?id={post_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["id"] == post_id

    def test_get_post_not_found(self, client):
        resp = client.get("/api/v1/post?id=999999")
        assert resp.status_code == 404

    def test_edit_post_requires_auth(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="editauthhash")
            post_id = post.id

        resp = client.put(
            "/api/v1/post",
            data=json.dumps({"id": post_id, "source": "https://example.com"}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 403)

    def test_edit_post_as_admin(self, admin_client, make_post, app):
        client, user = admin_client
        with app.app_context():
            post = make_post(sha256_hash="editadminhash")
            post_id = post.id

        resp = client.put(
            "/api/v1/post",
            data=json.dumps({"id": post_id, "source": "https://newexample.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["source"] == "https://newexample.com"

    def test_get_posts_pagination(self, client, make_post, app):
        with app.app_context():
            for i in range(5):
                make_post(sha256_hash=f"pagehash{i}")

        resp = client.get("/api/v1/posts?per_page=2&page=1")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["data"]) <= 2

    def test_deepdanbooru_status_reports_disabled(self, client, app, monkeypatch):
        monkeypatch.setitem(app.config, "DEEPDANBOORU_ENABLED", False)

        resp = client.get("/api/v1/posts/auto-tags/status")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["available"] is False
        assert data["enabled"] is False

    def test_deepdanbooru_status_reports_missing_tensorflow_io(self, client, app, monkeypatch):
        import onani.services.deepdanbooru as dd_module

        monkeypatch.setitem(app.config, "DEEPDANBOORU_ENABLED", True)
        monkeypatch.setitem(app.config, "DEEPDANBOORU_PROJECT_PATH", "/tmp")

        def fake_find_spec(name):
            if name == "tensorflow_io":
                return None
            return object()

        monkeypatch.setattr(dd_module.importlib.util, "find_spec", fake_find_spec)
        monkeypatch.setattr(dd_module.os.path, "isdir", lambda _path: True)
        monkeypatch.setattr(dd_module.os.path, "isfile", lambda _path: True)

        resp = client.get("/api/v1/posts/auto-tags/status")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["available"] is False
        assert data["reason"] == "Python package 'tensorflow-io' is not installed."

    def test_deepdanbooru_suggests_tags_for_post(self, admin_client, make_post, app, monkeypatch):
        import onani.routes.api.v1.posts as posts_module

        client, _user = admin_client
        with app.app_context():
            post = make_post(sha256_hash="ddposthash1")
            post_id = post.id

        monkeypatch.setattr(
            posts_module,
            "suggest_labels_for_post",
            lambda post, config, threshold=None: {
                "tags": [
                    {"name": "1girl", "tag": "1girl", "type": "general", "score": 0.97, "exists": True},
                    {"name": "smile", "tag": "smile", "type": "general", "score": 0.83, "exists": True},
                ],
                "rating": "q",
                "rating_score": 0.991,
            },
        )

        resp = client.post(
            "/api/v1/posts/auto-tags",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert [item["tag"] for item in data["data"]] == ["1girl", "smile"]
        assert data["rating"] == "q"
        assert data["rating_score"] == 0.991

    def test_deepdanbooru_filters_new_tags_for_regular_users(self, logged_in_client, make_post, app, monkeypatch):
        import onani.routes.api.v1.posts as posts_module
        from onani.models import User

        client, user = logged_in_client
        with app.app_context():
            uploader = User.query.filter_by(id=user.id).first()
            post = make_post(uploader=uploader, sha256_hash="ddposthash2")
            post_id = post.id

        monkeypatch.setattr(
            posts_module,
            "suggest_labels_for_post",
            lambda post, config, threshold=None: {
                "tags": [
                    {"name": "existing_tag", "tag": "existing_tag", "type": "general", "score": 0.91, "exists": True},
                    {"name": "new_tag", "tag": "new_tag", "type": "general", "score": 0.88, "exists": False},
                ],
                "rating": "e",
                "rating_score": 0.9,
            },
        )

        resp = client.post(
            "/api/v1/posts/auto-tags",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert [item["tag"] for item in data["data"]] == ["existing_tag"]
        assert data["rating"] == "e"

    def test_deepdanbooru_missing_payload_returns_clear_error(self, admin_client):
        client, _user = admin_client

        resp = client.post(
            "/api/v1/posts/auto-tags",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["message"] == "Provide either multipart file or JSON post_id."

    def test_deepdanbooru_multipart_without_file_returns_clear_error(self, admin_client):
        client, _user = admin_client

        resp = client.post(
            "/api/v1/posts/auto-tags",
            data={"threshold": "0.7"},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert data["message"] == "No file provided."


class TestVoteAPI:
    def test_vote_requires_login(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="votehash1")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/vote",
            data=json.dumps({"post_id": post_id, "type": "upvote"}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 302)

    def test_upvote_post(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="upvotehash1")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/vote",
            data=json.dumps({"post_id": post_id, "type": "upvote"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "score" in data
        assert data["has_upvoted"] is True

    def test_upvote_toggle(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="upvotehash2")
            post_id = post.id

        # Upvote
        client.post(
            "/api/v1/posts/vote",
            data=json.dumps({"post_id": post_id, "type": "upvote"}),
            content_type="application/json",
        )
        # Upvote again (should toggle off)
        resp = client.post(
            "/api/v1/posts/vote",
            data=json.dumps({"post_id": post_id, "type": "upvote"}),
            content_type="application/json",
        )
        data = json.loads(resp.data)
        assert data["has_upvoted"] is False



class TestWaterAPI:
    def test_water_requires_login(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="waterhash1")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/water",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 302)

    def test_water_increments_count(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="waterhash2")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/water",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["water_count"] == 1

    def test_water_keeps_incrementing(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="waterhash3")
            post_id = post.id

        for _ in range(3):
            client.post(
                "/api/v1/posts/water",
                data=json.dumps({"post_id": post_id}),
                content_type="application/json",
            )
        resp = client.post(
            "/api/v1/posts/water",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        data = json.loads(resp.data)
        assert data["water_count"] == 4

    def test_post_get_returns_has_favourited(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="waterhash4")
            post_id = post.id

        resp = client.get(f"/api/v1/post?id={post_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "has_favourited" in data
        assert data["has_favourited"] is False

    def test_favourite_requires_login(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="favhash0")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/favourite",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 302)

    def test_favourite_post(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="favhash1")
            post_id = post.id

        resp = client.post(
            "/api/v1/posts/favourite",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["has_favourited"] is True

    def test_favourite_toggle_off(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="favhash2")
            post_id = post.id

        payload = json.dumps({"post_id": post_id})
        client.post("/api/v1/posts/favourite", data=payload, content_type="application/json")
        resp = client.post("/api/v1/posts/favourite", data=payload, content_type="application/json")
        data = json.loads(resp.data)
        assert data["has_favourited"] is False

    def test_favourites_listing(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="favhash3")
            post_id = post.id

        client.post(
            "/api/v1/posts/favourite",
            data=json.dumps({"post_id": post_id}),
            content_type="application/json",
        )

        resp = client.get("/api/v1/posts/favourites")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        ids = [p["id"] for p in data["data"]]
        assert post_id in ids

    def test_favourites_empty_after_unfavourite(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="favhash4")
            post_id = post.id

        payload = json.dumps({"post_id": post_id})
        # Favourite then unfavourite
        for _ in range(2):
            client.post("/api/v1/posts/favourite", data=payload, content_type="application/json")

        resp = client.get("/api/v1/posts/favourites")
        data = json.loads(resp.data)
        ids = [p["id"] for p in data["data"]]
        assert post_id not in ids

    def test_favourites_listing_requires_login(self, client):
        resp = client.get("/api/v1/posts/favourites")
        assert resp.status_code in (401, 302)


class TestTagsAPI:
    def test_get_tags_empty(self, client):
        resp = client.get("/api/v1/tags")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_get_single_tag(self, client, make_tag, app):
        with app.app_context():
            tag = make_tag("apitag")
            tag_id = tag.id

        resp = client.get(f"/api/v1/tags?id={tag_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["name"] == "apitag"

    def test_get_tag_not_found(self, client):
        resp = client.get("/api/v1/tags?id=999999")
        assert resp.status_code == 404

    def test_tags_sorted_by_post_count_desc(self, client, make_tag, app):
        with app.app_context():
            make_tag("lowcount")
            make_tag("highcount")

        resp = client.get("/api/v1/tags?sort=post_count&order=desc")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_tags_sorted_by_name_asc(self, client, make_tag, app):
        with app.app_context():
            make_tag("zebra_tag")
            make_tag("ant_tag")

        resp = client.get("/api/v1/tags?sort=name&order=asc")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_tag_autocomplete(self, client, make_tag, app):
        with app.app_context():
            make_tag("autocomplete_test")

        resp = client.get("/api/v1/tags/autocomplete?query=autocomp")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data
        names = [t["name"] for t in data["data"]]
        assert any("autocomplete" in n for n in names)


class TestCommentsAPI:
    def test_get_comments_for_post(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="comhash1")
            post_id = post.id

        resp = client.get(f"/api/v1/comments?post_id={post_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_create_comment_requires_login(self, client, make_post, app):
        with app.app_context():
            post = make_post(sha256_hash="comhash2")
            post_id = post.id

        resp = client.post(
            "/api/v1/comments",
            data=json.dumps({"post_id": post_id, "content": "Hello"}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 302)

    def test_create_comment_success(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="comhash3")
            post_id = post.id

        resp = client.post(
            "/api/v1/comments",
            data=json.dumps({"post_id": post_id, "content": "Nice post!"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["content"] == "Nice post!"

    def test_create_comment_too_long(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="comhash4")
            post_id = post.id

        resp = client.post(
            "/api/v1/comments",
            data=json.dumps({"post_id": post_id, "content": "x" * 2001}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_delete_comment_requires_permission(self, logged_in_client, make_post, make_user, app):
        """Regular user should not be able to delete comments."""
        from onani.models import PostComment

        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="delhash1")
            commenter = make_user(username="commentauthor")
            comment = PostComment()
            comment.author = commenter
            comment.post = post
            comment.content = "I wrote this"
            from onani import db as _db
            _db.session.add(comment)
            _db.session.commit()
            comment_id = comment.id

        resp = client.delete(
            "/api/v1/comments",
            data=json.dumps({"comment_id": comment_id}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_delete_comment_as_moderator(self, admin_client, make_post, make_user, app):
        """Admin/mod should be able to delete comments."""
        from onani.models import PostComment

        client, admin = admin_client
        with app.app_context():
            post = make_post(sha256_hash="delhash2")
            commenter = make_user(username="commentauthor2")
            comment = PostComment()
            comment.author = commenter
            comment.post = post
            comment.content = "Delete me"
            from onani import db as _db
            _db.session.add(comment)
            _db.session.commit()
            comment_id = comment.id

        resp = client.delete(
            "/api/v1/comments",
            data=json.dumps({"comment_id": comment_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_create_reply_comment_success(self, logged_in_client, make_post, make_user, app):
        from onani.models import PostComment
        from onani import db as _db

        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="comreplyhash1")
            commenter = make_user(username="replyparentuser1")
            parent = PostComment(author=commenter, post=post, content="Parent")
            _db.session.add(parent)
            _db.session.commit()
            post_id = post.id
            parent_id = parent.id

        resp = client.post(
            "/api/v1/comments",
            data=json.dumps({"post_id": post_id, "parent_id": parent_id, "content": "Child reply"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["parent_id"] == parent_id
        assert data["content"] == "Child reply"

    def test_create_reply_comment_wrong_parent_post(self, logged_in_client, make_post, make_user, app):
        from onani.models import PostComment
        from onani import db as _db

        client, user = logged_in_client
        with app.app_context():
            parent_post = make_post(sha256_hash="comreplyhash2")
            target_post = make_post(sha256_hash="comreplyhash3")
            commenter = make_user(username="replyparentuser2")
            parent = PostComment(author=commenter, post=parent_post, content="Parent")
            _db.session.add(parent)
            _db.session.commit()
            target_post_id = target_post.id
            parent_id = parent.id

        resp = client.post(
            "/api/v1/comments",
            data=json.dumps({"post_id": target_post_id, "parent_id": parent_id, "content": "Invalid reply"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_comment_upvote_toggle(self, logged_in_client, make_post, make_user, app):
        from onani.models import PostComment
        from onani import db as _db

        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="comvotehash1")
            commenter = make_user(username="commentvoterauthor")
            comment = PostComment(author=commenter, post=post, content="Vote me")
            _db.session.add(comment)
            _db.session.commit()
            comment_id = comment.id

        first = client.post(
            "/api/v1/comments/upvote",
            data=json.dumps({"comment_id": comment_id}),
            content_type="application/json",
        )
        assert first.status_code == 200
        first_data = json.loads(first.data)
        assert first_data["upvote_count"] == 1
        assert first_data["has_upvoted"] is True

        second = client.post(
            "/api/v1/comments/upvote",
            data=json.dumps({"comment_id": comment_id}),
            content_type="application/json",
        )
        assert second.status_code == 200
        second_data = json.loads(second.data)
        assert second_data["upvote_count"] == 0
        assert second_data["has_upvoted"] is False


class TestNewsAPI:
    def test_get_news_empty(self, client):
        resp = client.get("/api/v1/news")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_get_news_with_articles(self, client, app):
        from onani.models import NewsPost, NewsType, User, UserSettings

        with app.app_context():
            user = User(username="newsauthor")
            user.set_password("pass")
            user.settings = UserSettings()
            from onani import db as _db
            _db.session.add(user)
            _db.session.commit()

            article = NewsPost()
            article.author = user
            article.title = "Test News Article"
            article.content = "Content here"
            _db.session.add(article)
            _db.session.commit()

        resp = client.get("/api/v1/news")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["data"]) >= 1


class TestProfileAPI:
    def test_profile_requires_login(self, client):
        resp = client.get("/api/v1/profile")
        assert resp.status_code in (401, 302)

    def test_get_profile(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/api/v1/profile")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "username" in data
        assert "email" in data

    def test_update_nickname(self, logged_in_client, app):
        client, user = logged_in_client
        resp = client.put(
            "/api/v1/profile",
            data=json.dumps({"nickname": "My New Nick"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["nickname"] == "My New Nick"

    def test_update_password_wrong_current(self, logged_in_client, app):
        client, user = logged_in_client
        resp = client.put(
            "/api/v1/profile",
            data=json.dumps({
                "current_password": "wrongcurrent",
                "new_password": "newpassword",
            }),
            content_type="application/json",
        )
        # Password change should silently fail if current is wrong - user returned unchanged
        assert resp.status_code == 200

    def test_patch_same_as_put(self, logged_in_client):
        client, user = logged_in_client
        resp = client.patch(
            "/api/v1/profile",
            data=json.dumps({"nickname": "Patched Nick"}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_remove_profile_picture_flag(self, logged_in_client, app):
        client, user = logged_in_client
        with app.app_context():
            user.settings.avatar = "/avatars/test-avatar.png"
            from onani import db as _db
            _db.session.commit()

        resp = client.put(
            "/api/v1/profile",
            data=json.dumps({"remove_profile_picture": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["settings"]["avatar"] is None

    def test_disable_otp_requires_password(self, logged_in_client, app):
        client, user = logged_in_client
        with app.app_context():
            user.otp_enabled = True
            from onani import db as _db
            _db.session.commit()

        resp = client.delete(
            "/api/v1/profile/otp",
            data=json.dumps({"password": "wrong-password"}),
            content_type="application/json",
        )
        assert resp.status_code == 403


class TestCollectionsAPI:
    def test_list_collections_empty(self, client):
        resp = client.get("/api/v1/collections")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_create_collection_requires_login(self, client):
        resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "Should Fail"}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 403)

    def test_create_and_get_collection(self, logged_in_client, app):
        client, user = logged_in_client
        resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "My Collection", "description": "desc"}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["title"] == "My Collection"
        collection_id = data["id"]

        resp2 = client.get(f"/api/v1/collections?id={collection_id}")
        assert resp2.status_code == 200
        data2 = json.loads(resp2.data)
        assert data2["id"] == collection_id

    def test_get_collection_not_found(self, client):
        resp = client.get("/api/v1/collections?id=999999")
        assert resp.status_code == 404

    def test_update_collection_title(self, logged_in_client, app):
        client, user = logged_in_client
        create_resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "Old Title"}),
            content_type="application/json",
        )
        collection_id = json.loads(create_resp.data)["id"]

        resp = client.put(
            "/api/v1/collections",
            data=json.dumps({"id": collection_id, "title": "New Title"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "New Title"

    def test_delete_collection(self, logged_in_client, app):
        client, user = logged_in_client
        create_resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "To Delete"}),
            content_type="application/json",
        )
        collection_id = json.loads(create_resp.data)["id"]

        del_resp = client.delete(
            "/api/v1/collections",
            data=json.dumps({"id": collection_id}),
            content_type="application/json",
        )
        assert del_resp.status_code == 204

    def test_delete_other_user_collection_forbidden(self, logged_in_client, app, make_user):
        """A regular user cannot delete another user's collection."""
        client, user = logged_in_client
        with app.app_context():
            from onani import db as _db
            from onani.models import Collection
            other = make_user(username="other_coll_owner", password="pass")
            collection = Collection(
                title="Other's Collection",
                creator=other.id,
            )
            _db.session.add(collection)
            _db.session.commit()
            collection_id = collection.id

        resp = client.delete(
            "/api/v1/collections",
            data=json.dumps({"id": collection_id}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_add_post_to_collection(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="collposttest1")
            post_id = post.id

        create_resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "Post Collection"}),
            content_type="application/json",
        )
        collection_id = json.loads(create_resp.data)["id"]

        resp = client.post(
            "/api/v1/collections/posts",
            data=json.dumps({"collection_id": collection_id, "post_id": post_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert any(p["id"] == post_id for p in data["posts"])

    def test_remove_post_from_collection(self, logged_in_client, make_post, app):
        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="collposttest2")
            post_id = post.id

        create_resp = client.post(
            "/api/v1/collections",
            data=json.dumps({"title": "Post Removal Collection"}),
            content_type="application/json",
        )
        collection_id = json.loads(create_resp.data)["id"]

        client.post(
            "/api/v1/collections/posts",
            data=json.dumps({"collection_id": collection_id, "post_id": post_id}),
            content_type="application/json",
        )

        del_resp = client.delete(
            "/api/v1/collections/posts",
            data=json.dumps({"collection_id": collection_id, "post_id": post_id}),
            content_type="application/json",
        )
        assert del_resp.status_code == 200
        data = json.loads(del_resp.data)
        assert not any(p["id"] == post_id for p in data["posts"])


class TestAdminUserEditAPI:
    def test_get_user_requires_auth(self, client, make_user, app):
        with app.app_context():
            target = make_user(username="edittarget1")
            target_id = target.id
        resp = client.get(f"/api/v1/admin/user?user_id={target_id}")
        assert resp.status_code in (401, 403)

    def test_get_user_requires_edit_users_permission(self, logged_in_client, make_user, app):
        with app.app_context():
            target = make_user(username="edittarget2")
            target_id = target.id
        client, user = logged_in_client
        resp = client.get(f"/api/v1/admin/user?user_id={target_id}")
        assert resp.status_code in (401, 403)

    def test_get_user_as_admin(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="edittarget3", email="target3@example.com")
            target_id = target.id
        client, _ = admin_client
        resp = client.get(f"/api/v1/admin/user?user_id={target_id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["id"] == target_id
        assert data["username"] == "edittarget3"
        assert "permissions_int" in data
        assert "role_int" in data

    def test_get_user_not_found(self, admin_client):
        client, _ = admin_client
        resp = client.get("/api/v1/admin/user?user_id=999999")
        assert resp.status_code == 404

    def test_put_change_nickname(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="nickedit1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "nickname": "CoolNick"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["nickname"] == "CoolNick"

    def test_put_change_email(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="emailedit1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "email": "new@example.com"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["email"] == "new@example.com"

    def test_put_reset_password(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="pwreset1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "password": "newpassword123"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        with app.app_context():
            from onani.models import User
            u = User.query.get(target_id)
            assert u.check_password("newpassword123")

    def test_put_password_too_short(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="pwshort1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "password": "short"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_put_change_role(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="roleedit1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "role": "MODERATOR"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["role_int"] == 200

    def test_put_change_permissions(self, admin_client, make_user, app):
        with app.app_context():
            target = make_user(username="permedit1")
            target_id = target.id
        client, _ = admin_client
        new_perms = 1 | 32 | 65536  # CREATE_POSTS | CREATE_TAGS | CREATE_COMMENTS
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "permissions": new_perms}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["permissions_int"] == new_perms

    def test_put_cannot_edit_equal_role(self, admin_client, make_user, app):
        """An admin cannot edit another user with an equal or higher role."""
        from onani.models import UserRoles, UserPermissions
        with app.app_context():
            peer = make_user(
                username="peereditor",
                role=UserRoles.ADMIN,
                permissions=UserPermissions.ADMINISTRATION,
            )
            peer_id = peer.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": peer_id, "nickname": "Hacked"}),
            content_type="application/json",
        )
        assert resp.status_code == 403

    def test_put_cannot_assign_equal_role(self, admin_client, make_user, app):
        """Admin cannot promote someone to ADMIN (same as their own role)."""
        with app.app_context():
            target = make_user(username="promote1")
            target_id = target.id
        client, _ = admin_client
        resp = client.put(
            "/api/v1/admin/user",
            data=json.dumps({"user_id": target_id, "role": "ADMIN"}),
            content_type="application/json",
        )
        assert resp.status_code == 403


class TestAdminAPI:
    def test_stats_requires_auth(self, client):
        resp = client.get("/api/v1/admin/stats")
        assert resp.status_code in (401, 403)

    def test_stats_requires_moderator(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/api/v1/admin/stats")
        assert resp.status_code in (401, 403)

    def test_stats_as_admin(self, admin_client):
        client, user = admin_client
        resp = client.get("/api/v1/admin/stats")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        for key in (
            "posts",
            "posts_hidden",
            "posts_imported",
            "posts_with_source",
            "posts_tag_request",
            "posts_last_24h",
            "users",
            "users_deleted",
            "users_banned_active",
            "users_last_24h",
            "tags",
            "collections",
            "comments",
            "comments_last_24h",
            "errors",
            "ratings",
            "imports",
            "scheduled_imports",
        ):
            assert key in data

        for key in ("general", "questionable", "sensitive", "explicit"):
            assert key in data["ratings"]

        for key in ("total", "active", "queued", "success", "failed", "revoked"):
            assert key in data["imports"]

        for key in ("total", "enabled", "disabled"):
            assert key in data["scheduled_imports"]

    def test_celery_logs_requires_auth(self, client):
        resp = client.get("/api/v1/admin/celery-logs")
        assert resp.status_code in (401, 403)

    def test_celery_logs_as_admin_no_file(self, admin_client, tmp_path, monkeypatch):
        """When the log file does not exist the endpoint returns available=False."""
        import onani.routes.api.v1._admin.stats as stats_module
        monkeypatch.setattr(stats_module.AdminCeleryLogs, "LOG_PATH", str(tmp_path / "missing.log"))
        client, user = admin_client
        resp = client.get("/api/v1/admin/celery-logs?lines=50")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["available"] is False

    def test_celery_logs_returns_lines(self, admin_client, tmp_path, monkeypatch):
        """When the log file exists the endpoint returns the last N lines."""
        import onani.routes.api.v1._admin.stats as stats_module
        log_file = tmp_path / "celery.log"
        log_file.write_text("\n".join(f"line {i}" for i in range(200)))
        monkeypatch.setattr(stats_module.AdminCeleryLogs, "LOG_PATH", str(log_file))
        client, user = admin_client
        resp = client.get("/api/v1/admin/celery-logs?lines=50")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["available"] is True
        assert len(data["lines"]) <= 50

    def test_deepdanbooru_task_dispatches(self, admin_client, monkeypatch):
        client, _user = admin_client
        monkeypatch.setattr(
            "onani.services.deepdanbooru.get_deepdanbooru_status",
            lambda config: {"available": True, "reason": None},
        )
        monkeypatch.setattr(
            "onani.tasks.deepdanbooru.deepdanbooru_tag_tag_request_posts.apply_async",
            lambda: SimpleNamespace(id="dd-task-123"),
        )

        resp = client.post(
            "/api/v1/admin/tasks",
            data=json.dumps({"task": "deepdanbooru_tag_posts"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["task_id"] == "dd-task-123"
        assert "queued" in data["message"].lower()

    def test_deepdanbooru_all_posts_task_dispatches(self, admin_client, monkeypatch):
        client, _user = admin_client
        monkeypatch.setattr(
            "onani.services.deepdanbooru.get_deepdanbooru_status",
            lambda config: {"available": True, "reason": None},
        )
        monkeypatch.setattr(
            "onani.tasks.deepdanbooru.deepdanbooru_tag_all_posts.apply_async",
            lambda: SimpleNamespace(id="dd-all-task-123"),
        )

        resp = client.post(
            "/api/v1/admin/tasks",
            data=json.dumps({"task": "deepdanbooru_tag_all_posts"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["task_id"] == "dd-all-task-123"
        assert "queued" in data["message"].lower()

    def test_deepdanbooru_task_updates_post_rating(self, app, make_post, make_tag, monkeypatch):
        from onani.models import Post, PostRating
        from onani.tasks.deepdanbooru import deepdanbooru_tag_all_posts

        with app.app_context():
            tag_request = make_tag(name="tag_request")
            post = make_post(sha256_hash="ddratingtaskhash", rating=PostRating.GENERAL, tags=[tag_request])
            post_id = post.id

            monkeypatch.setattr(
                "onani.services.deepdanbooru.suggest_labels_for_post",
                lambda _post, _config: {
                    "tags": [],
                    "rating": "e",
                    "rating_score": 0.98,
                },
            )

            result = deepdanbooru_tag_all_posts.run()
            updated = Post.query.filter_by(id=post_id).first()

            assert updated.rating == PostRating.EXPLICIT
            assert result["updated_ratings"] >= 1

    def test_generate_all_thumbnails_task_runs(self, admin_client, monkeypatch):
        client, _user = admin_client
        monkeypatch.setattr(
            "onani.tasks.thumbnails.generate_all_thumbnails.apply_async",
            lambda: SimpleNamespace(id="thumb-task-123"),
        )

        resp = client.post(
            "/api/v1/admin/tasks",
            data=json.dumps({"task": "generate_all_thumbnails"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["task_id"] == "thumb-task-123"
        assert "queued" in data["message"].lower()


class TestImportAPI:
    def test_import_status_unknown_task(self, logged_in_client):
        """Querying an unknown task ID returns a PENDING status."""
        client, user = logged_in_client
        resp = client.get("/api/v1/import?id=nonexistent-task-id-12345")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "PENDING"

    def test_import_requires_login(self, client):
        resp = client.post(
            "/api/v1/import",
            data=json.dumps({"url": "https://example.com/img.jpg"}),
            content_type="application/json",
        )
        assert resp.status_code in (401, 403)
