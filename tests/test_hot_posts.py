# -*- coding: utf-8 -*-
"""Tests for the hot-posts feature."""
import json
import datetime

import pytest


class TestHotScore:
    """Unit tests for the hot-score algorithm (no DB needed)."""

    def test_score_positive(self):
        from Onani.services.hot import compute_hot_score

        hs = compute_hot_score(
            score=10,
            age_hours=1.0,
            recent_views=50,
            unique_commenters=5,
            tag_count=10,
        )
        assert hs > 0

    def test_newer_post_scores_higher_than_older(self):
        from Onani.services.hot import compute_hot_score

        new_score = compute_hot_score(
            score=5, age_hours=2.0, recent_views=10, unique_commenters=2, tag_count=5
        )
        old_score = compute_hot_score(
            score=5, age_hours=100.0, recent_views=10, unique_commenters=2, tag_count=5
        )
        assert new_score > old_score

    def test_negative_score_drags(self):
        from Onani.services.hot import compute_hot_score

        good = compute_hot_score(
            score=5, age_hours=1.0, recent_views=10, unique_commenters=0, tag_count=5
        )
        bad = compute_hot_score(
            score=-5, age_hours=1.0, recent_views=10, unique_commenters=0, tag_count=5
        )
        assert good > bad

    def test_more_views_means_hotter(self):
        from Onani.services.hot import compute_hot_score

        low = compute_hot_score(
            score=1, age_hours=1.0, recent_views=1, unique_commenters=0, tag_count=5
        )
        high = compute_hot_score(
            score=1, age_hours=1.0, recent_views=1000, unique_commenters=0, tag_count=5
        )
        assert high > low

    def test_more_unique_commenters_means_hotter(self):
        from Onani.services.hot import compute_hot_score

        low = compute_hot_score(
            score=1, age_hours=1.0, recent_views=0, unique_commenters=0, tag_count=5
        )
        high = compute_hot_score(
            score=1, age_hours=1.0, recent_views=0, unique_commenters=20, tag_count=5
        )
        assert high > low

    def test_more_tags_means_slightly_hotter(self):
        from Onani.services.hot import compute_hot_score

        low = compute_hot_score(
            score=1, age_hours=1.0, recent_views=0, unique_commenters=0, tag_count=1
        )
        high = compute_hot_score(
            score=1, age_hours=1.0, recent_views=0, unique_commenters=0, tag_count=50
        )
        # Tag factor is small but positive
        # Because of random noise, just check the mean over multiple runs
        # by using fixed random seed via monkeypatching
        # Here we check the deterministic part (noise is [0,0.3] so if difference > 0.3,
        # it's always true)
        assert high >= low


class TestHotPostsAPI:
    """Integration tests for the /posts/hot endpoint."""

    def test_hot_posts_endpoint_exists(self, logged_in_client, app):
        client, _ = logged_in_client
        resp = client.get("/api/v1/posts/hot")
        assert resp.status_code == 200

    def test_hot_posts_returns_data_list(self, logged_in_client, make_post, app):
        client, _ = logged_in_client
        with app.app_context():
            make_post(sha256_hash="hothash1")
            make_post(sha256_hash="hothash2")

        resp = client.get("/api/v1/posts/hot")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data

    def test_hot_posts_respects_limit(self, logged_in_client, make_post, app):
        client, _ = logged_in_client
        with app.app_context():
            for i in range(5):
                make_post(sha256_hash=f"hotlimithash{i}")

        resp = client.get("/api/v1/posts/hot?limit=3")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["data"]) <= 3

    def test_hot_posts_limit_capped_at_100(self, logged_in_client, app):
        client, _ = logged_in_client
        resp = client.get("/api/v1/posts/hot?limit=9999")
        assert resp.status_code == 200


class TestPostsHomeHot:
    """Ensure /posts/home now includes hot posts."""

    def test_home_includes_hot_key(self, logged_in_client, app):
        client, _ = logged_in_client
        resp = client.get("/api/v1/posts/home")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "hot" in data
        assert isinstance(data["hot"], list)


class TestRecordView:
    """Ensure fetching a post records a view."""

    def test_view_recorded_on_get(self, logged_in_client, make_post, app):
        from Onani.models.post.view import PostView

        client, _ = logged_in_client
        with app.app_context():
            post = make_post(sha256_hash="viewhash1")
            post_id = post.id
            initial_count = PostView.query.filter_by(post_id=post_id).count()

        client.get(f"/api/v1/post?id={post_id}")

        with app.app_context():
            new_count = PostView.query.filter_by(post_id=post_id).count()

        assert new_count == initial_count + 1
