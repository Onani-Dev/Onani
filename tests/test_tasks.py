# -*- coding: utf-8 -*-
"""Tests for Celery tasks in Onani/tasks/."""
import pytest


class TestDeleteUserPostsTask:
    def test_deletes_all_user_posts(self, app, db, make_user, make_post):
        from Onani.models import Post
        from Onani.tasks.database import delete_user_posts

        user = make_user(username="taskuser1")
        post1 = make_post(uploader=user, sha256_hash="taskhash1")
        post2 = make_post(uploader=user, sha256_hash="taskhash2")

        result = delete_user_posts(user.id)

        assert result["deleted"] == 2
        assert Post.query.filter_by(id=post1.id).first() is None
        assert Post.query.filter_by(id=post2.id).first() is None

    def test_returns_zero_for_user_with_no_posts(self, app, db, make_user):
        from Onani.tasks.database import delete_user_posts

        user = make_user(username="taskuser2")
        result = delete_user_posts(user.id)

        assert result["deleted"] == 0

    def test_returns_error_for_missing_user(self, app, db):
        from Onani.tasks.database import delete_user_posts

        result = delete_user_posts(99999)

        assert result["deleted"] == 0
        assert "error" in result
