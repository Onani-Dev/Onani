# -*- coding: utf-8 -*-
"""Tests for Post model, Tag model, and their relationships."""
import pytest


class TestPostModel:
    def test_post_score_empty(self, app, db, make_post):
        post = make_post(sha256_hash="scorehash1")
        assert post.score == 0

    def test_post_title_no_tags(self, app, db, make_post):
        post = make_post(sha256_hash="titlehash1")
        assert post.title == f"#{post.id}"

    def test_post_title_with_character_tag(self, app, db, make_post, make_tag):
        from onani.models.tag.type import TagType

        # "test_character" -> humanized -> "test character" -> capitalize() -> "Test character"
        char_tag = make_tag("test_character", TagType.CHARACTER)
        post = make_post(sha256_hash="titlehash2", tags=[char_tag])
        assert "Test character" in post.title

    def test_post_title_with_artist_tag(self, app, db, make_post, make_tag):
        from onani.models.tag.type import TagType

        artist_tag = make_tag("some_artist", TagType.ARTIST)
        post = make_post(sha256_hash="titlehash3", tags=[artist_tag])
        assert "drawn by" in post.title

    def test_post_tag_string(self, app, db, make_post, make_tag):
        tag1 = make_tag("tag_one")
        tag2 = make_tag("tag_two")
        post = make_post(sha256_hash="tagstrhash1", tags=[tag1, tag2])
        ts = post.tag_string
        assert "tag_one" in ts
        assert "tag_two" in ts

    def test_post_is_safe(self, app, db, make_post):
        from onani.models.post.rating import PostRating

        safe_post = make_post(sha256_hash="safehash1", rating=PostRating.GENERAL)
        assert safe_post.is_safe is True

        explicit_post = make_post(sha256_hash="explhash1", rating=PostRating.EXPLICIT)
        assert explicit_post.is_safe is False

    def test_post_is_imported(self, app, db, make_user):
        from onani.models import Post
        from onani.models.post.rating import PostRating

        user = make_user(username="importeruser")
        post = Post(
            uploader=user,
            filename="importhash.png",
            sha256_hash="importhash",
            md5_hash="immd5",
            width=800, height=600,
            filesize=50000,
            file_type="png",
            rating=PostRating.GENERAL,
            original_filename="original.png",
            imported_from="https://danbooru.donmai.us/posts/12345",
        )
        db.session.add(post)
        db.session.commit()
        assert post.is_imported is True

    def test_post_source_html_escaped(self, app, db, make_user):
        from onani.models import Post
        from onani.models.post.rating import PostRating

        user = make_user(username="srcescuser")
        post = Post(
            uploader=user,
            filename="srchash.png",
            sha256_hash="srchash",
            md5_hash="srcmd5",
            width=100, height=100,
            filesize=1000,
            file_type="png",
            rating=PostRating.GENERAL,
            original_filename="orig.png",
            source="<script>alert(1)</script>",
        )
        db.session.add(post)
        db.session.commit()
        assert "<script>" not in post.source

    def test_post_duplicate_sha256_rejected(self, app, db, make_post):
        from onani.models import Post, User, UserSettings
        from onani.models.post.rating import PostRating

        make_post(sha256_hash="duphash1")
        user = User(username="dupuploader")
        user.set_password("pass")
        user.settings = UserSettings()
        db.session.add(user)
        db.session.commit()

        with pytest.raises(ValueError, match="already exists"):
            p2 = Post(
                uploader=user,
                filename="duphash1x.png",
                sha256_hash="duphash1",  # duplicate
                md5_hash="diffmd5",
                width=100, height=100,
                filesize=1000,
                file_type="png",
                rating=PostRating.GENERAL,
                original_filename="orig.png",
            )
            db.session.add(p2)

    def test_post_sorted_tags_by_type(self, app, db, make_post, make_tag):
        from onani.models.tag.type import TagType

        artist = make_tag("painter", TagType.ARTIST)
        char = make_tag("hero", TagType.CHARACTER)
        general = make_tag("blue_sky")
        post = make_post(sha256_hash="sortedhash1", tags=[artist, char, general])
        sorted_tags = post.sorted_tags
        assert TagType.ARTIST in sorted_tags
        assert TagType.CHARACTER in sorted_tags
        assert TagType.GENERAL in sorted_tags


class TestTagModel:
    def test_tag_humanized(self, app, db, make_tag):
        tag = make_tag("hello_world")
        assert tag.humanized == "hello world"

    def test_tag_text_format_general(self, app, db, make_tag):
        tag = make_tag("blue_hair")
        assert tag.text_format == "blue_hair"

    def test_tag_text_format_typed(self, app, db, make_tag):
        from onani.models.tag.type import TagType

        tag = make_tag("picasso", TagType.ARTIST)
        assert tag.text_format == "artist:picasso"

    def test_tag_is_alias_false(self, app, db, make_tag):
        tag = make_tag("notanalias")
        assert tag.is_alias is False

    def test_tag_is_alias_true(self, app, db, make_tag):
        from onani.models import Tag

        original = make_tag("original_tag")
        alias = Tag(name="alias_tag", alias_of=original.id)
        db.session.add(alias)
        db.session.commit()
        assert alias.is_alias is True

    def test_tag_post_count_increments(self, app, db, make_post, make_tag):
        tag = make_tag("countable_tag")
        initial = tag.post_count
        make_post(sha256_hash="counthash1", tags=[tag])
        tag.recount_posts()
        db.session.commit()
        assert tag.post_count == initial + 1


class TestPostComment:
    def test_create_comment(self, app, db, make_user, make_post):
        from onani.models import PostComment

        user = make_user(username="commenter")
        post = make_post(sha256_hash="commenthash1")
        comment = PostComment()
        comment.author = user
        comment.post = post
        comment.content = "Great post!"
        db.session.add(comment)
        db.session.commit()
        assert comment.id is not None
        assert comment.content == "Great post!"

    def test_comment_too_long(self, app, db, make_user, make_post):
        from onani.models import PostComment

        user = make_user(username="longcommenter")
        post = make_post(sha256_hash="commenthash2")
        comment = PostComment()
        comment.author = user
        comment.post = post
        with pytest.raises(ValueError, match="too long"):
            comment.content = "x" * 2001

    def test_comment_collapses_newlines(self, app, db, make_user, make_post):
        from onani.models import PostComment

        user = make_user(username="newlinecommenter")
        post = make_post(sha256_hash="commenthash3")
        comment = PostComment()
        comment.author = user
        comment.post = post
        comment.content = "line1\n\n\n\n\nline2"
        db.session.add(comment)
        db.session.commit()
        assert "\n\n\n\n" not in comment.content

    def test_comment_html_escaped(self, app, db, make_user, make_post):
        from onani.models import PostComment

        user = make_user(username="htmlcommenter")
        post = make_post(sha256_hash="commenthash4")
        comment = PostComment()
        comment.author = user
        comment.post = post
        comment.content = "<script>alert(1)</script>"
        db.session.add(comment)
        db.session.commit()
        assert "<script>" not in comment.content


class TestBanModel:
    def test_ban_has_expired_false(self, app, db, make_user):
        import datetime
        from onani.models import Ban

        user = make_user(username="notexpireduser")
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        ban = Ban(user=user.id, expires=future, reason="Test")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is False

    def test_ban_has_expired_true(self, app, db, make_user):
        import datetime
        from onani.models import Ban

        user = make_user(username="expiredbanuser")
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        ban = Ban(user=user.id, expires=past, reason="Test")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is True

    def test_ban_no_expiry_never_expires(self, app, db, make_user):
        from onani.models import Ban

        user = make_user(username="permabanuser")
        ban = Ban(user=user.id, expires=None, reason="Permanent ban")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is False
