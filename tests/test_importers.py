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

    def test_known_site_sizebooru_post(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://sizebooru.com/Details/12345")

    def test_known_site_sizebooru_gallery(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://sizebooru.com/Galleries/List/1039")

    def test_known_site_sizebooru_tags(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import is_supported
            assert is_supported("https://sizebooru.com/Search/giantess")

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
    def test_run_job_enables_global_metadata_config(self, mock_datajob_cls, app):
        """_run_job sets gallery-dl metadata=True globally for all extractors."""
        with app.app_context():
            from gallery_dl import config as gdl_config
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://sizebooru.com/Picture/12345"]
            mock_job.data_meta = [{}]
            mock_job.data_post = [{"tags": ["giantess"], "rating": "q"}]
            mock_datajob_cls.return_value = mock_job

            get_post("https://sizebooru.com/Details/12345")

            assert gdl_config.get(("extractor",), "metadata") is True

    @patch("gallery_dl.job.DataJob")
    def test_run_job_times_out_raises(self, mock_datajob_cls, app):
        """get_post raises GalleryDLTimeoutError when the DataJob exceeds _JOB_TIMEOUT."""
        import threading
        with app.app_context():
            from Onani.importers import gallery_dl_importer as gdl_mod
            from Onani.importers.gallery_dl_importer import GalleryDLTimeoutError

            barrier = threading.Event()

            def _hang():
                barrier.wait(timeout=10)

            mock_job = MagicMock()
            mock_job.run.side_effect = _hang
            mock_datajob_cls.return_value = mock_job

            orig_timeout = gdl_mod._JOB_TIMEOUT
            gdl_mod._JOB_TIMEOUT = 0.05  # 50 ms — instant for tests
            try:
                with pytest.raises(GalleryDLTimeoutError):
                    gdl_mod.get_post("https://sizebooru.com/Details/12345")
            finally:
                gdl_mod._JOB_TIMEOUT = orig_timeout
                barrier.set()

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

    @patch("gallery_dl.job.DataJob")
    def test_get_post_userName_becomes_artist_tag(self, mock_datajob_cls, app):
        """userName field (RedGifs / community sites) is tagged as artist:."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/video.mp4"]
            mock_job.data_meta = [{"userName": "teamsavage792", "category": "redgifs"}]
            mock_job.data_post = [{"tags": ["Amateur"], "userName": "teamsavage792", "category": "redgifs"}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://redgifs.com/watch/abc123")
            assert result is not None
            assert "artist:teamsavage792" in result.tags

    @patch("gallery_dl.job.DataJob")
    def test_get_post_category_not_used_as_collection(self, mock_datajob_cls, app):
        """'category' (site name) must NOT become the collection name."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.example.com/video.mp4"]
            mock_job.data_meta = [{"userName": "teamsavage792", "category": "redgifs"}]
            mock_job.data_post = [{"tags": [], "userName": "teamsavage792", "category": "redgifs"}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://redgifs.com/watch/abc123")
            assert result is not None
            assert result.collection_name != "redgifs"
            # No niches → no collection
            assert result.collection_name is None

    @patch("gallery_dl.job.DataJob")
    def test_get_post_redgifs_niche_becomes_collection(self, mock_datajob_cls, app):
        """RedGifs post with a niche uses the niche as the collection name."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://cdn.redgifs.com/video.mp4"]
            mock_job.data_meta = [{"userName": "someone", "category": "redgifs", "niches": ["Amateur"]}]
            mock_job.data_post = [{"tags": [], "userName": "someone", "category": "redgifs", "niches": ["Amateur"]}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://redgifs.com/watch/xyz")
            assert result is not None
            assert result.collection_name == "Amateur"

    @patch("gallery_dl.job.DataJob")
    def test_get_post_subreddit_becomes_collection(self, mock_datajob_cls, app):
        """subreddit key maps to the collection name."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_post

            mock_job = MagicMock()
            mock_job.data_urls = ["https://i.redd.it/abc.jpg"]
            mock_job.data_meta = [{"subreddit": "gonewild", "author": "redditor123"}]
            mock_job.data_post = [{"tags": [], "subreddit": "gonewild", "author": "redditor123"}]
            mock_datajob_cls.return_value = mock_job

            result = get_post("https://reddit.com/r/gonewild/comments/abc/")
            assert result is not None
            assert result.collection_name == "gonewild"

    @patch("gallery_dl.job.DataJob")
    def test_get_all_posts_returns_multiple(self, mock_datajob_cls, app):
        """get_all_posts returns one ImportedPost per file URL."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import get_all_posts

            mock_job = MagicMock()
            mock_job.data_urls = [
                "https://cdn.example.com/img1.jpg",
                "https://cdn.example.com/img2.jpg",
                "https://cdn.example.com/img3.jpg",
            ]
            mock_job.data_meta = [{}, {}, {}]
            mock_job.data_post = [{"tags": ["test"], "title": "My Gallery", "rating": "q"}]
            mock_datajob_cls.return_value = mock_job

            results = get_all_posts("https://www.pixiv.net/en/artworks/99999")
            assert len(results) == 3
            assert all(r.collection_name == "My Gallery" for r in results)


class TestExtractCollectionName:
    """Unit tests for _extract_collection_name helper."""

    def test_community_key_subreddit(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            meta = {"subreddit": "cats", "category": "reddit"}
            assert _extract_collection_name(meta, "https://reddit.com/...", False) == "cats"

    def test_community_key_userName(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            # RedGifs with no niches → None (userName is ignored for redgifs)
            meta = {"userName": "artist_xyz", "category": "redgifs"}
            assert _extract_collection_name(meta, "https://redgifs.com/...", False) is None

    def test_redgifs_niche_used_as_collection(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            meta = {"userName": "artist_xyz", "category": "redgifs", "niches": ["Amateur", "MILF"]}
            assert _extract_collection_name(meta, "https://redgifs.com/...", False) == "Amateur"

    def test_category_not_matched(self, app):
        """'category' is intentionally excluded from _COMMUNITY_KEYS."""
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            meta = {"category": "redgifs"}
            assert _extract_collection_name(meta, "https://redgifs.com/...", False) is None

    def test_gallery_key_only_for_multi(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            meta = {"album": "My Album"}
            # single=False → gallery keys ignored
            assert _extract_collection_name(meta, "https://example.com/...", False) is None
            # multi=True → gallery key used
            assert _extract_collection_name(meta, "https://example.com/...", True) == "My Album"

    def test_empty_meta_returns_none_for_single(self, app):
        with app.app_context():
            from Onani.importers.gallery_dl_importer import _extract_collection_name
            assert _extract_collection_name({}, "https://example.com/", False) is None


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
