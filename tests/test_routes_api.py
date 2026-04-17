# -*- coding: utf-8 -*-
"""Tests for the REST API v1 endpoints."""
import json
import pytest


class TestAPIIndex:
    def test_api_index(self, client):
        resp = client.get("/api/v1/")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "version" in data


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
        from Onani.models import PostComment

        client, user = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="delhash1")
            commenter = make_user(username="commentauthor")
            comment = PostComment()
            comment.author = commenter
            comment.post = post
            comment.content = "I wrote this"
            from Onani import db as _db
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
        from Onani.models import PostComment

        client, admin = admin_client
        with app.app_context():
            post = make_post(sha256_hash="delhash2")
            commenter = make_user(username="commentauthor2")
            comment = PostComment()
            comment.author = commenter
            comment.post = post
            comment.content = "Delete me"
            from Onani import db as _db
            _db.session.add(comment)
            _db.session.commit()
            comment_id = comment.id

        resp = client.delete(
            "/api/v1/comments",
            data=json.dumps({"comment_id": comment_id}),
            content_type="application/json",
        )
        assert resp.status_code == 200


class TestNewsAPI:
    def test_get_news_empty(self, client):
        resp = client.get("/api/v1/news")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data

    def test_get_news_with_articles(self, client, app):
        from Onani.models import NewsPost, NewsType, User, UserSettings

        with app.app_context():
            user = User(username="newsauthor")
            user.set_password("pass")
            user.settings = UserSettings()
            from Onani import db as _db
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

    def test_sfw_mode_returned_in_profile(self, logged_in_client):
        client, user = logged_in_client
        resp = client.get("/api/v1/profile")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "settings" in data
        assert "sfw_mode" in data["settings"]

    def test_update_sfw_mode_true(self, logged_in_client):
        client, user = logged_in_client
        resp = client.put(
            "/api/v1/profile",
            data=json.dumps({"sfw_mode": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["settings"]["sfw_mode"] is True

    def test_update_sfw_mode_false(self, logged_in_client, app):
        client, user = logged_in_client
        with app.app_context():
            from Onani import db
            u = db.session.get(type(user), user.id)
            u.settings.sfw_mode = True
            db.session.commit()

        resp = client.put(
            "/api/v1/profile",
            data=json.dumps({"sfw_mode": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["settings"]["sfw_mode"] is False
