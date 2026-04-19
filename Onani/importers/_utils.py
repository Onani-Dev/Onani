# -*- coding: utf-8 -*-

import http.cookiejar
import logging
from typing import Optional

import requests
from curl_cffi import requests as cffi_requests
from flask import current_app
from Onani.services.posts import create_post
from Onani.services.files import get_file_data, get_video_data, is_video_url, detect_video_format
from Onani.models import Post, User

from ._importedpost import ImportedPost
from . import db


def get_post(url: str) -> Optional[ImportedPost]:
    """Fetch post metadata from a URL via gallery-dl.

    Returns an ImportedPost on success, or None if the URL is not supported.
    """
    from .gallery_dl_importer import get_post as gdl_get_post, is_supported

    if not is_supported(url):
        return None

    return gdl_get_post(url)


def get_all_posts(url: str, cookies_path: str = None) -> list:
    """Fetch all posts from a URL (gallery support).

    Returns a list of ImportedPost objects — multiple for galleries, one for single posts.
    """
    from .gallery_dl_importer import get_all_posts as gdl_get_all_posts, is_supported

    if not is_supported(url):
        return []

    return gdl_get_all_posts(url, cookies_path=cookies_path)


_DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
}

import re as _re

log = logging.getLogger(__name__)

# Byte prefixes that indicate an HTML/JSON error page rather than binary media
_TEXT_PREFIXES = (b"<!doctype", b"<html", b"{", b"[")

# Danbooru CDN original URL pattern:
#   https://cdn.donmai.us/original/{a}/{b}/{hash}.{ext}
# Sample URL pattern (publicly accessible without Gold):
#   https://cdn.donmai.us/sample/{a}/{b}/sample-{hash}.jpg
_DANBOORU_ORIGINAL_RE = _re.compile(
    r"(https://cdn\.donmai\.us)/original/([0-9a-f]{2}/[0-9a-f]{2})/([0-9a-f]+)\.[^/?#]+"
)

# Kemono CDN node pattern — URLs are https://n{1-4}.kemono.cr/data/...
_KEMONO_NODE_RE = _re.compile(r"https://n(\d+)\.kemono\.cr/(.+)")
_KEMONO_NODES = list(range(1, 5))  # n1 … n4


def _danbooru_sample_url(original_url: str) -> str | None:
    """Convert a Danbooru /original/ URL to its /sample/ equivalent, or return None."""
    m = _DANBOORU_ORIGINAL_RE.match(original_url)
    if not m:
        return None
    base, dirs, hash_ = m.group(1), m.group(2), m.group(3)
    return f"{base}/sample/{dirs}/sample-{hash_}.jpg"


def _load_cookiejar(cookies_path: str) -> http.cookiejar.CookieJar:
    """Load a Netscape-format cookies file into a CookieJar."""
    jar = http.cookiejar.MozillaCookieJar()
    try:
        jar.load(cookies_path, ignore_discard=True, ignore_expires=True)
    except (http.cookiejar.LoadError, OSError):
        pass
    return jar


def _kemono_alt_urls(url: str) -> list[str]:
    """Return alternative kemono CDN node URLs for *url*, excluding the original node."""
    m = _KEMONO_NODE_RE.match(url)
    if not m:
        return []
    failed_node = int(m.group(1))
    path = m.group(2)
    return [
        f"https://n{n}.kemono.cr/{path}"
        for n in _KEMONO_NODES
        if n != failed_node
    ]


def _fetch(session: cffi_requests.Session, url: str, headers: dict) -> cffi_requests.Response:
    """GET *url*, with fallbacks for Danbooru sample URLs and kemono CDN nodes."""
    try:
        r = session.get(url, headers=headers, timeout=60)
    except Exception as exc:
        # Connection-level failure (curl error 7, timeout, etc.).
        # Try alternate kemono CDN nodes before giving up.
        alt_urls = _kemono_alt_urls(url)
        last_exc = exc
        for alt in alt_urls:
            log.debug("Connection failed on %s, retrying on %s", url, alt)
            try:
                r = session.get(alt, headers=headers, timeout=60)
                break
            except Exception as alt_exc:
                last_exc = alt_exc
        else:
            raise last_exc

    if r.status_code == 403:
        sample_url = _danbooru_sample_url(url)
        if sample_url:
            log.debug("403 on original, retrying with sample: %s", sample_url)
            r = session.get(sample_url, headers=headers, timeout=60)
    r.raise_for_status()
    return r


def download_file(url: str, cookies_path: str = None, referer: str = None) -> bytes:
    headers = dict(_DOWNLOAD_HEADERS)
    if referer:
        headers["Referer"] = referer
    with cffi_requests.Session(impersonate="chrome") as s:
        if cookies_path:
            jar = _load_cookiejar(cookies_path)
            for cookie in jar:
                s.cookies.set(cookie.name, cookie.value, domain=cookie.domain)
        r = _fetch(s, url, headers)
        data = r.content
    for prefix in _TEXT_PREFIXES:
        if data[: len(prefix)].lower() == prefix:
            raise ValueError(
                f"Server returned non-binary content for {url!r} "
                f"(starts with {data[:64]!r})"
            )
    return data


def save_imported_post(post: ImportedPost, importer_id: int, cookies_path: str = None) -> Post:
    from PIL import UnidentifiedImageError
    from .gallery_dl_importer import is_supported, get_post as _gdl_resolve

    # If the file_url is itself a gallery-dl-supported page (e.g. a RedGifs
    # watch URL embedded inside a Reddit post), resolve it to the actual media
    # URL before attempting to download.  gallery-dl's Reddit extractor often
    # returns embedded cross-site URLs verbatim rather than following them
    # through the target site's extractor.
    file_url = post.file_url
    if is_supported(file_url):
        resolved = _gdl_resolve(file_url)
        if resolved and resolved.file_url:
            file_url = resolved.file_url
            # Absorb any extra tags the target-site extractor found
            for tag in resolved.tags:
                if tag not in post.tags:
                    post.tags.append(tag)

    file_data = download_file(file_url, cookies_path=cookies_path, referer=post.imported_url)

    # Detect video format — first by URL extension, then by magic bytes
    video_fmt = None
    if is_video_url(file_url):
        video_fmt = file_url.split("?")[0].rsplit(".", 1)[-1].lower()
    else:
        video_fmt = detect_video_format(file_data)

    if video_fmt:
        (
            image_file,
            filesize,
            hash_sha256,
            hash_md5,
            width,
            height,
            filename,
            file_type,
        ) = get_video_data(file_data, input_format=video_fmt)
    else:
        # Try PIL; if it can't identify the file, try as an mp4 last resort
        try:
            import io as _io
            from PIL import Image as _Image
            _Image.open(_io.BytesIO(file_data)).verify()
        except UnidentifiedImageError:
            (
                image_file,
                filesize,
                hash_sha256,
                hash_md5,
                width,
                height,
                filename,
                file_type,
            ) = get_video_data(file_data, input_format="mp4")
        else:
            (
                image_file,
                filesize,
                hash_sha256,
                hash_md5,
                width,
                height,
                filename,
                file_type,
            ) = get_file_data(file_data)

    user = User.query.filter_by(id=importer_id).first()
    can_create_tags = True

    return create_post(
        post.sources[0],
        post.description,
        user,
        post.rating.value,
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
        "Unknown",
        post.tags,
        images_dir=current_app.config["IMAGES_DIR"],
        can_create_tags=can_create_tags,
        tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
        post_min_tags=current_app.config["POST_MIN_TAGS"],
        imported_from=post.imported_url,
    )
