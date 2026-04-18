# -*- coding: utf-8 -*-
"""
gallery-dl integration — catch-all importer for 900+ sites.

gallery-dl's DataJob is used to extract a file URL and post metadata without
writing anything to disk. The result is mapped to an ImportedPost.

Sites already handled by a specific importer (danbooru, rule34, etc.) are
resolved before this module is consulted, so there is no duplication.

Per-site authentication and cookies can be configured by pointing
``GALLERY_DL_CONFIG_FILE`` at a standard gallery-dl config.json file.
"""
from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import List, Optional

from gallery_dl import config as gdl_config
from gallery_dl import extractor as gdl_extractor
from gallery_dl import job as gdl_job

from Onani.models import PostRating

from ._importedpost import ImportedPost

log = logging.getLogger(__name__)

# Map the various rating strings gallery-dl extractors can emit to PostRating
_RATING_MAP: dict[str, PostRating] = {
    "g": PostRating.GENERAL,
    "s": PostRating.GENERAL,
    "safe": PostRating.GENERAL,
    "general": PostRating.GENERAL,
    "q": PostRating.QUESTIONABLE,
    "questionable": PostRating.QUESTIONABLE,
    "e": PostRating.EXPLICIT,
    "explicit": PostRating.EXPLICIT,
}


@lru_cache(maxsize=None)
def _init_gdl_config(config_file: str | None) -> None:
    """Load a gallery-dl config file exactly once per distinct path.

    ``lru_cache`` ensures this is a no-op on every call after the first one,
    avoiding repeated IO in long-running workers.
    """
    if config_file:
        gdl_config.load([config_file])


def is_supported(url: str) -> bool:
    """Return True if gallery-dl has an extractor that matches *url*.

    This only pattern-matches the URL — no network request is made.
    """
    return gdl_extractor.find(url) is not None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _as_list(value) -> List[str]:
    """Normalise a value that may be a list, space-separated string, or None."""
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v]
    return str(value).split()


def _extract_tags(kwdict: dict) -> List[str]:
    """Build a typed tag list from a gallery-dl keyword dict.

    gallery-dl extractors use different field names across sites, so we try
    several common variants. Tags are returned in the ``type:name`` format
    expected by Onani's tag parser.
    """
    tags: List[str] = []

    # Generic tags — may be a list or a space-separated string
    raw = kwdict.get("tags", [])
    if isinstance(raw, (list, tuple)):
        tags.extend(str(t) for t in raw if t)
    elif isinstance(raw, str) and raw:
        tags.extend(raw.split())

    # Artist / author — booru-style sites use "artist"; community sites use "author"
    for artist in _as_list(kwdict.get("artist")):
        tags.append(f"artist:{artist}")

    # Community post author (Reddit, Twitter, RedGifs, etc.) — tagged as "artist"
    # when there is no explicit artist field.
    if not kwdict.get("artist"):
        for author in _as_list(
            kwdict.get("userName")      # RedGifs
            or kwdict.get("author")     # Reddit, generic
            or kwdict.get("uploader")   # various
            or kwdict.get("user")       # Twitter/X, others
        ):
            tags.append(f"artist:{author}")

    # Character
    for char in _as_list(kwdict.get("characters") or kwdict.get("character")):
        tags.append(f"character:{char}")

    # Copyright / series
    for copy_ in _as_list(kwdict.get("copyrights") or kwdict.get("copyright")):
        tags.append(f"copyright:{copy_}")

    return [t for t in tags if t]


# Community-style keys that identify a "group/channel" the post belongs to.
# These are used as the collection name for single posts too.
_COMMUNITY_KEYS = ("subreddit", "community", "board", "channel", "group", "userName", "user")

# Gallery-style keys (collections only make sense for multi-file URLs)
_GALLERY_KEYS = ("title", "gallery", "album", "pool", "set", "collection")


def _extract_collection_name(meta: dict, url: str, multi: bool) -> Optional[str]:
    """Return a collection name derived from *meta*, or None.

    Community keys (subreddit, board, …) are checked for every import.
    Gallery keys (album, pool, …) are only used when *multi* is True.

    RedGifs special case: only use a niche as the collection name. A post
    that belongs to no niche gets no collection, regardless of uploader.
    """
    # RedGifs: collection only if the post belongs to a niche
    if meta.get("category") == "redgifs":
        niches = meta.get("niches") or []
        if isinstance(niches, (list, tuple)) and niches:
            return str(niches[0]).strip() or None
        return None

    # Community first — applies to single posts too
    for key in _COMMUNITY_KEYS:
        val = meta.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    if not multi:
        return None

    # Gallery-level name for multi-file imports
    for key in _GALLERY_KEYS:
        val = meta.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    # URL-derived fallback for galleries
    from urllib.parse import urlparse
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1] if path else url


def _extract_rating(kwdict: dict) -> PostRating:
    """Map a gallery-dl rating string to a PostRating enum value.

    Defaults to QUESTIONABLE when the rating is absent or unrecognised.
    """
    raw = kwdict.get("rating", "q")
    if isinstance(raw, str):
        return _RATING_MAP.get(raw.lower().strip(), PostRating.QUESTIONABLE)
    return PostRating.QUESTIONABLE


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def _run_job(url: str, cookies_path: str = None) -> Optional[gdl_job.DataJob]:
    """Run a gallery-dl DataJob and return it, or None on failure."""
    from flask import current_app

    config_file: str | None = current_app.config.get("GALLERY_DL_CONFIG_FILE")
    _init_gdl_config(config_file)

    # Inject cookies file into gallery-dl config if provided
    if cookies_path:
        gdl_config.set((), "cookies", cookies_path)

    try:
        djob = gdl_job.DataJob(url, file=io.StringIO())
        djob.run()
    except Exception:
        log.exception("gallery-dl DataJob failed for %s", url)
        return None

    if not djob.data_urls:
        log.debug("gallery-dl found no file URLs for %s", url)
        return None

    return djob


def _build_post(url: str, file_url: str, kwdict: dict, post_meta: dict) -> ImportedPost:
    tags = _extract_tags(post_meta)
    rating = _extract_rating(post_meta)
    description = str(post_meta.get("description") or post_meta.get("comment") or "")

    sources: List[str] = [url]
    ext_source = post_meta.get("source") or kwdict.get("source")
    if ext_source and str(ext_source) != url:
        sources.insert(0, str(ext_source))

    return ImportedPost(
        imported_url=url,
        tags=tags,
        sources=sources,
        file_url=file_url,
        description=description,
        rating=rating,
    )


def get_post(url: str, cookies_path: str = None) -> Optional[ImportedPost]:
    """Fetch the first post from a URL. Returns None if unsupported."""
    djob = _run_job(url, cookies_path=cookies_path)
    if djob is None:
        return None

    file_url: str = djob.data_urls[0]
    kwdict: dict = djob.data_meta[0] if djob.data_meta else {}
    post_meta: dict = djob.data_post[0] if djob.data_post else kwdict
    merged = {**post_meta, **kwdict}

    p = _build_post(url, file_url, kwdict, merged)
    p.collection_name = _extract_collection_name(merged, url, multi=False)
    return p


def get_all_posts(url: str, cookies_path: str = None) -> List[ImportedPost]:
    """Fetch ALL posts/files from a URL (gallery support).

    Returns a list of :class:`ImportedPost` — one per file found. For a
    single-image URL this will be a list of length 1. Returns an empty list
    if the URL is unsupported or an error occurs.
    """
    djob = _run_job(url, cookies_path=cookies_path)
    if djob is None:
        return []

    # Shared gallery-level metadata (artist, rating, etc.)
    gallery_meta: dict = djob.data_post[0] if djob.data_post else {}
    multi = len(djob.data_urls) > 1

    # Derive a collection name from the first item's merged metadata
    first_kwdict = djob.data_meta[0] if djob.data_meta else {}
    combined_meta = {**gallery_meta, **first_kwdict}
    collection_name = _extract_collection_name(combined_meta, url, multi=multi)

    posts: List[ImportedPost] = []
    for i, file_url in enumerate(djob.data_urls):
        kwdict: dict = djob.data_meta[i] if i < len(djob.data_meta) else {}
        # Per-file metadata takes priority; fall back to gallery-level
        post_meta = {**gallery_meta, **kwdict}
        p = _build_post(url, file_url, kwdict, post_meta)
        if collection_name:
            p.collection_name = collection_name
        posts.append(p)

    return posts
