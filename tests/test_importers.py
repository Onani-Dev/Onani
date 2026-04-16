# -*- coding: utf-8 -*-
"""Tests for importer modules."""
import pytest
from unittest.mock import MagicMock, patch


class TestIsSupported:
    def test_known_site_danbooru(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://danbooru.donmai.us/posts/12345")

    def test_known_site_gelbooru(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://gelbooru.com/index.php?page=post&s=view&id=1")

    def test_known_site_rule34(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://rule34.xxx/index.php?page=post&s=view&id=1")

    def test_unsupported_site_returns_false(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert not is_supported("https://unknown-site.example.com/post/123")

    def test_invalid_url_returns_false(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert not is_supported("not-a-url-at-all")


class TestGalleryDlImporter:
    """Tests for the gallery-dl catch-all importer module."""

    def test_is_supported_known_site(self, app):
        """gallery-dl should recognise well-known sites like pixiv."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://www.pixiv.net/en/artworks/12345")

    def test_is_unsupported_site_returns_false(self, app):
        """Completely unknown domains should not be matched."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert not is_supported("https://unknown-site-xyz.example.com/post/1")

    @patch("gallery_dl.job.DataJob")
    def test_get_post_returns_imported_post(self, mock_datajob_cls, app):
        """get_post maps gallery-dl data correctly to an ImportedPost."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post
            from Onani.models import PostRating

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
            mock_job.data_meta = [{"tags": ["tag1", "tag2"], "rating": "q"}]
            mock_job.data_post = [{"tags": ["tag1", "tag2"], "rating": "q", "description": "a post"}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")

            assert result is not None
            assert result.file_url == "https://cdn.example.com/image.jpg"
            assert result.rating == PostRating.QUESTIONABLE
            assert "tag1" in result.tags
            assert "tag2" in result.tags

    @patch("gallery_dl.job.DataJob")
    def test_get_post_no_urls_returns_none(self, mock_datajob_cls, app):
        """get_post returns None when gallery-dl finds no file URLs."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = []
            mock_job.data_meta = []
            mock_job.data_post = []
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is None

    @patch("gallery_dl.job.DataJob")
    def test_get_post_maps_explicit_rating(self, mock_datajob_cls, app):
        """'explicit' and 'e' gallery-dl rating strings map to PostRating.EXPLICIT."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post
            from Onani.models import PostRating

            for rating_str in ("e", "explicit"):
                mock_job = MagicMock()
                mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
                mock_job.data_meta = [{}]
                mock_job.data_post = [{"rating": rating_str, "tags": []}]
                mock_datajob_cls.return_value = mock_job

                result = get_post("https://www.pixiv.net/en/artworks/12345")
                assert result is not None
                assert result.rating == PostRating.EXPLICIT, f"Expected EXPLICIT for rating '{rating_str}'"

    @patch("gallery_dl.job.DataJob")
    def test_get_post_maps_artist_tags(self, mock_datajob_cls, app):
        """Artist names from kwdict are prefixed with 'artist:' in the tag list."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
            mock_job.data_meta = [{}]
            mock_job.data_post = [{"artist": ["john_doe"], "rating": "s", "tags": []}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is not None
            assert "artist:john_doe" in result.tags

    @patch("gallery_dl.job.DataJob")
    def test_get_post_maps_character_and_copyright_tags(self, mock_datajob_cls, app):
        """Character and copyright fields are prefixed correctly."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
            mock_job.data_meta = [{}]
            mock_job.data_post = [{
                "characters": ["alice", "bob"],
                "copyrights": ["some_series"],
                "rating": "g",
                "tags": [],
            }]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is not None
            assert "character:alice" in result.tags
            assert "character:bob" in result.tags
            assert "copyright:some_series" in result.tags

    @patch("gallery_dl.job.DataJob")
    def test_get_post_includes_external_source(self, mock_datajob_cls, app):
        """A 'source' field in post metadata is prepended to sources list."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
            mock_job.data_meta = [{}]
            mock_job.data_post = [{"source": "https://original.example.com/post/1", "tags": []}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is not None
            assert "https://original.example.com/post/1" in result.sources
            assert "https://www.pixiv.net/en/artworks/12345" in result.sources

    @patch("gallery_dl.job.DataJob")
    def test_get_post_exception_returns_none(self, mock_datajob_cls, app):
        """A gallery-dl exception is caught and None is returned."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.run.side_effect = Exception("network error")
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is None

    @patch("gallery_dl.job.DataJob")
    def test_get_post_string_tags_split_correctly(self, mock_datajob_cls, app):
        """Space-separated string tags are split into individual entries."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/image.jpg"]
            mock_job.data_meta = [{}]
            mock_job.data_post = [{"tags": "foo bar baz", "rating": "q"}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://www.pixiv.net/en/artworks/12345")
            assert result is not None
            assert "foo" in result.tags
            assert "bar" in result.tags
            assert "baz" in result.tags


class TestGetPostGalleryDlFallback:
    """Tests that _utils.get_post falls back to gallery-dl for unsupported sites."""

    @patch("Onani.importers.gallery_dl_importer.get_post")
    @patch("Onani.importers.gallery_dl_importer.is_supported")
    def test_falls_back_to_gallery_dl_for_unrecognised_url(
        self, mock_is_supported, mock_gdl_get_post, app
    ):
        """URLs with no specific importer are tried against gallery-dl."""
        with app.app_context():
            from Onani.importers._utils import get_post
            from Onani.models import PostRating

            mock_is_supported.return_value = True
            fake_post = MagicMock()
            fake_post.file_url = "https://example.com/img.jpg"
            fake_post.rating = PostRating.GENERAL
            mock_gdl_get_post.return_value = fake_post

            result = get_post("https://twitter.com/user/status/12345678")
            mock_gdl_get_post.assert_called_once()
            assert result is fake_post

    @patch("Onani.importers.gallery_dl_importer.get_post")
    @patch("Onani.importers.gallery_dl_importer.is_supported")
    def test_returns_none_when_gallery_dl_does_not_support_url(
        self, mock_is_supported, mock_gdl_get_post, app
    ):
        """None is returned when gallery-dl doesn't match."""
        with app.app_context():
            from Onani.importers._utils import get_post

            mock_is_supported.return_value = False

            result = get_post("https://totally-unknown.example.com/post/99")
            mock_gdl_get_post.assert_not_called()
            assert result is None
