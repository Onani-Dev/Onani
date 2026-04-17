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
        from Onani.models.tag.type import TagType

        # "test_character" -> humanized -> "test character" -> capitalize() -> "Test character"
        char_tag = make_tag("test_character", TagType.CHARACTER)
        post = make_post(sha256_hash="titlehash2", tags=[char_tag])
        assert "Test character" in post.title

    def test_post_title_with_artist_tag(self, app, db, make_post, make_tag):
        from Onani.models.tag.type import TagType

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
        from Onani.models.post.rating import PostRating

        safe_post = make_post(sha256_hash="safehash1", rating=PostRating.GENERAL)
        assert safe_post.is_safe is True

        explicit_post = make_post(sha256_hash="explhash1", rating=PostRating.EXPLICIT)
        assert explicit_post.is_safe is False

    def test_post_is_imported(self, app, db, make_user):
        from Onani.models import Post
        from Onani.models.post.rating import PostRating
        from Onani.models.post.status import PostStatus

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
            status=PostStatus.APPROVED,
            original_filename="original.png",
            imported_from="https://danbooru.donmai.us/posts/12345",
        )
        db.session.add(post)
        db.session.commit()
        assert post.is_imported is True

    def test_post_source_html_escaped(self, app, db, make_user):
        from Onani.models import Post
        from Onani.models.post.rating import PostRating
        from Onani.models.post.status import PostStatus

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
            status=PostStatus.APPROVED,
            original_filename="orig.png",
            source="<script>alert(1)</script>",
        )
        db.session.add(post)
        db.session.commit()
        assert "<script>" not in post.source

    def test_post_duplicate_sha256_rejected(self, app, db, make_post):
        from Onani.models import Post, User, UserSettings
        from Onani.models.post.rating import PostRating
        from Onani.models.post.status import PostStatus

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
                status=PostStatus.APPROVED,
                original_filename="orig.png",
            )
            db.session.add(p2)

    def test_post_phash_stored(self, app, db, make_post):
        """A post created with a phash value should persist it."""
        post = make_post(sha256_hash="phashhash1", phash="aabbccdd11223344")
        assert post.phash == "aabbccdd11223344"

    def test_post_phash_nullable(self, app, db, make_post):
        """phash may be None (e.g. for video posts)."""
        post = make_post(sha256_hash="phashhash2", phash=None)
        assert post.phash is None

    def test_post_sorted_tags_by_type(self, app, db, make_post, make_tag):
        from Onani.models.tag.type import TagType

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
        from Onani.models.tag.type import TagType

        tag = make_tag("picasso", TagType.ARTIST)
        assert tag.text_format == "artist:picasso"

    def test_tag_is_alias_false(self, app, db, make_tag):
        tag = make_tag("notanalias")
        assert tag.is_alias is False

    def test_tag_is_alias_true(self, app, db, make_tag):
        from Onani.models import Tag

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
        from Onani.models import PostComment

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
        from Onani.models import PostComment

        user = make_user(username="longcommenter")
        post = make_post(sha256_hash="commenthash2")
        comment = PostComment()
        comment.author = user
        comment.post = post
        with pytest.raises(ValueError, match="too long"):
            comment.content = "x" * 2001

    def test_comment_collapses_newlines(self, app, db, make_user, make_post):
        from Onani.models import PostComment

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
        from Onani.models import PostComment

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
        from Onani.models import Ban

        user = make_user(username="notexpireduser")
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        ban = Ban(user=user.id, expires=future, reason="Test")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is False

    def test_ban_has_expired_true(self, app, db, make_user):
        import datetime
        from Onani.models import Ban

        user = make_user(username="expiredbanuser")
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        ban = Ban(user=user.id, expires=past, reason="Test")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is True

    def test_ban_no_expiry_never_expires(self, app, db, make_user):
        from Onani.models import Ban

        user = make_user(username="permabanuser")
        ban = Ban(user=user.id, expires=None, reason="Permanent ban")
        db.session.add(ban)
        db.session.commit()
        assert ban.has_expired is False


class TestGetFileDataPhash:
    """Tests for perceptual hash (phash) computation in services.files.get_file_data."""

    def _make_png_bytes(self, width=8, height=8, color=(128, 128, 128)):
        """Return raw PNG bytes for a small solid-colour image."""
        import io as _io
        from PIL import Image as _Image

        img = _Image.new("RGB", (width, height), color=color)
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_get_file_data_returns_phash(self, app):
        """get_file_data() should return a non-empty phash string."""
        from Onani.services.files import get_file_data

        data = self._make_png_bytes()
        result = get_file_data(data)
        assert len(result) == 9
        hash_phash = result[8]
        assert isinstance(hash_phash, str)
        assert len(hash_phash) > 0

    def test_identical_images_same_phash(self, app):
        """Two identical images must produce the same phash."""
        from Onani.services.files import get_file_data

        data = self._make_png_bytes(color=(100, 150, 200))
        phash1 = get_file_data(data)[8]
        phash2 = get_file_data(data)[8]
        assert phash1 == phash2

    def test_different_images_likely_different_phash(self, app):
        """Clearly distinct images should (with high probability) have different phashes."""
        from Onani.services.files import get_file_data

        data_black = self._make_png_bytes(color=(0, 0, 0))
        data_white = self._make_png_bytes(color=(255, 255, 255))
        phash_black = get_file_data(data_black)[8]
        phash_white = get_file_data(data_white)[8]
        assert phash_black != phash_white

    def test_create_post_phash_duplicate_rejected(self, app, db, make_user, tmp_path):
        """create_post() must reject a second upload whose phash matches an existing post."""
        import io as _io
        from Onani.models import Post
        from Onani.models.post.rating import PostRating
        from Onani.models.post.status import PostStatus
        from Onani.services.posts import create_post

        user = make_user(username="phashduper")
        images_dir = str(tmp_path)

        # Insert the first post directly with a known phash
        p1 = Post(
            uploader=user,
            filename="phashfile1.png",
            sha256_hash="phashdupsha1",
            md5_hash="phashdupmd51",
            phash="deadbeefdeadbeef",
            width=8, height=8,
            filesize=100,
            file_type="png",
            rating=PostRating.GENERAL,
            status=PostStatus.APPROVED,
            original_filename="orig1.png",
        )
        db.session.add(p1)
        db.session.commit()

        # Trying to create a second post with the same phash but different SHA256
        # should raise ValueError
        import pytest as _pytest
        with _pytest.raises(ValueError, match="already exists"):
            create_post(
                source="",
                description="",
                uploader=user,
                rating=PostRating.GENERAL.value,
                image_file=_io.BytesIO(b"fake"),
                filesize=100,
                hash_sha256="phashdupsha2",  # different SHA256
                hash_md5="phashdupmd52",
                width=8,
                height=8,
                filename="phashfile2.png",
                file_type="png",
                original_filename="orig2.png",
                tags=set(),
                images_dir=images_dir,
                can_create_tags=True,
                tag_char_limit=100,
                post_min_tags=1,
                hash_phash="deadbeefdeadbeef",  # same phash → near-duplicate
            )
