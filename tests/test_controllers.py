# -*- coding: utf-8 -*-
"""Tests for controllers: create_ban, delete_ban, create_user, determine_meta_tags, query_posts."""
import pytest


class TestCreateUser:
    def test_create_user_basic(self, app, db):
        from onani.controllers.database.users import create_user

        user = create_user("ctrluser1", "password123")
        assert user.id is not None
        assert user.username == "ctrluser1"
        assert user.check_password("password123")

    def test_create_user_with_email(self, app, db):
        from onani.controllers.database.users import create_user

        user = create_user("ctrluser2", "pass", email="ctrl@example.com")
        assert user.email == "ctrl@example.com"

    def test_create_user_persisted(self, app, db):
        from onani.controllers.database.users import create_user
        from onani.models import User

        create_user("ctrluser3", "pass")
        found = User.query.filter_by(username="ctrluser3").first()
        assert found is not None


class TestDetermineMetaTags:
    def test_long_horizontal(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(6000, 200, 100, "png")
        assert "meta:long" in tags

    def test_long_vertical(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(200, 6000, 100, "png")
        assert "meta:long" in tags

    def test_extremely_high_resolution(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(10001, 10001, 100, "png")
        assert "meta:extremely_high_resolution" in tags

    def test_high_resolution(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(1920, 1440, 100, "png")
        assert "meta:high_resolution" in tags

    def test_low_resolution(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(400, 400, 100, "png")
        assert "meta:low_resolution" in tags

    def test_large_filesize(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 6_000_000, "png")
        assert "meta:large_filesize" in tags

    def test_extremely_large_filesize(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 20_000_000, "png")
        assert "meta:extremely_large_filesize" in tags

    def test_animated_gif(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 100, "gif")
        assert "meta:animated" in tags

    def test_tag_request_added_when_low_count(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 100, "png", tag_count=3)
        assert "meta:tag_request" in tags

    def test_tag_request_not_added_when_enough_tags(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 100, "png", tag_count=15)
        assert "meta:tag_request" not in tags

    def test_no_meta_tags_normal_image(self, app):
        from onani.controllers.database.files import determine_meta_tags
        tags = determine_meta_tags(800, 600, 1_000_000, "png", tag_count=15)
        assert "meta:long" not in tags
        assert "meta:low_resolution" not in tags
        assert "meta:animated" not in tags


class TestQueryPosts:
    def test_query_all_posts(self, app, db, make_post):
        from onani.controllers.database.queries import query_posts

        make_post(sha256_hash="qhash1")
        make_post(sha256_hash="qhash2")
        result = query_posts().all()
        assert len(result) >= 2

    def test_query_filters_hidden(self, app, db, make_post):
        from onani import db as _db
        from onani.controllers.database.queries import query_posts

        make_post(sha256_hash="qhash3")
        hidden_post = make_post(sha256_hash="qhash4")
        hidden_post.hidden = True
        _db.session.commit()

        visible = query_posts().all()
        ids = [p.id for p in visible]
        assert hidden_post.id not in ids

    def test_query_shows_hidden_when_requested(self, app, db, make_post):
        from onani import db as _db
        from onani.controllers.database.queries import query_posts

        hidden_post = make_post(sha256_hash="qhash5")
        hidden_post.hidden = True
        _db.session.commit()

        all_posts = query_posts(show_hidden=True).all()
        ids = [p.id for p in all_posts]
        assert hidden_post.id in ids

    def test_query_by_tags(self, app, db, make_post, make_tag):
        from onani.controllers.database.queries import query_posts

        tag = make_tag("filtered_tag")
        tagged_post = make_post(sha256_hash="qhash6", tags=[tag])
        make_post(sha256_hash="qhash7")

        results = query_posts(tags=["filtered_tag"]).all()
        assert len(results) == 1
        assert results[0].id == tagged_post.id


class TestCreateComment:
    def test_create_comment(self, app, db, make_user, make_post):
        from onani.controllers.database.posts import create_comment

        user = make_user(username="commenter2")
        post = make_post(sha256_hash="cchash1")
        comment = create_comment(user, post, "Test comment :+1:")
        assert comment.id is not None
        assert comment.content is not None


class TestBanController:
    def test_create_ban(self, app, db, make_user):
        import datetime
        from unittest.mock import patch

        from onani import db as _db
        from onani.controllers.database.bans import create_ban
        from onani.models import UserRoles, UserPermissions

        banner = make_user(
            username="banner",
            role=UserRoles.ADMIN,
            permissions=UserPermissions.ADMINISTRATION,
        )
        target = make_user(username="bantarget")

        with patch("onani.controllers.database.bans.current_user", banner):
            future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
            ban = create_ban(target.id, future, "Test reason", False, False)
            assert ban.id is not None
            assert ban.reason == "Test reason"

    def test_delete_ban(self, app, db, make_user):
        import datetime

        from onani import db as _db
        from onani.controllers.database.bans import delete_ban
        from onani.models import Ban

        user = make_user(username="unbanning")
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        ban = Ban(user=user.id, expires=future, reason="to be removed")
        _db.session.add(ban)
        user.ban = ban
        _db.session.commit()

        result = delete_ban(user.id)
        assert result.ban is None

    def test_ban_user_not_found(self, app, db, make_user):
        import datetime
        from unittest.mock import patch

        from onani.controllers.database.bans import create_ban
        from onani.models import UserRoles, UserPermissions
        from werkzeug.exceptions import NotFound

        banner = make_user(
            username="bannernotfound",
            role=UserRoles.ADMIN,
            permissions=UserPermissions.ADMINISTRATION,
        )
        with patch("onani.controllers.database.bans.current_user", banner):
            with pytest.raises(NotFound):
                create_ban(99999, None, "reason", False, False)
