#!/usr/bin/env python3
"""Download DeepDanbooru source images and write DeepDanbooru-friendly tag sidecars.

Outputs per image:
- image file
- image.<ext>.txt    (space-separated tags)
- image.<ext>.json   (metadata)

Archive:
- SQLite DB with downloaded source post IDs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) OnaniDeepDanbooruDatasetBuilder/1.0"
TIMEOUT = 30

DETAIL_RE = re.compile(r'href="/Details/(\d+)\?')
SEARCH_TAG_RE = re.compile(r'href="/Search/([^"]+)"')
PAGE_NO_RE = re.compile(r"[?&]pageNo=(\d+)")

EXT_BY_CONTENT_TYPE = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}


def _request_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _request_binary(url: str) -> tuple[bytes, str | None, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
        content_type = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        final_url = resp.geturl()
    return data, content_type or None, final_url


def _ensure_archive(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS downloaded (
            post_id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            downloaded_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def _already_downloaded(conn: sqlite3.Connection, post_id: int) -> bool:
    row = conn.execute("SELECT 1 FROM downloaded WHERE post_id = ?", (post_id,)).fetchone()
    return row is not None


def _mark_downloaded(conn: sqlite3.Connection, post_id: int, filename: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO downloaded(post_id, filename, downloaded_at) VALUES(?,?,?)",
        (post_id, filename, int(time.time())),
    )


def _normalize_tag(tag: str) -> str:
    return unescape(urllib.parse.unquote(tag)).strip().lower().replace(" ", "_")


def _parse_tags_from_detail(detail_html: str) -> list[str]:
    marker = "<h6>Related Tags</h6>"
    idx = detail_html.find(marker)
    if idx == -1:
        return []

    segment = detail_html[idx:]
    ul_start = segment.find("<ul")
    ul_end = segment.find("</ul>")
    if ul_start == -1 or ul_end == -1:
        return []

    tags_block = segment[ul_start:ul_end]
    tags = [_normalize_tag(t) for t in SEARCH_TAG_RE.findall(tags_block)]

    deduped: list[str] = []
    seen = set()
    for tag in tags:
        if not tag or tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag)
    return deduped


def _extract_post_ids(search_html: str) -> list[int]:
    ids = [int(v) for v in DETAIL_RE.findall(search_html)]
    deduped: list[int] = []
    seen = set()
    for post_id in ids:
        if post_id in seen:
            continue
        seen.add(post_id)
        deduped.append(post_id)
    return deduped


def _has_next_page(search_html: str, page_no: int) -> bool:
    next_page = page_no + 1
    for raw in PAGE_NO_RE.findall(search_html):
        if int(raw) == next_page:
            return True
    return False


def _ext_from_response(content_type: str | None, final_url: str) -> str:
    if content_type and content_type in EXT_BY_CONTENT_TYPE:
        return EXT_BY_CONTENT_TYPE[content_type]

    parsed = urllib.parse.urlparse(final_url)
    suffix = Path(parsed.path).suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "webp", "gif", "bmp", "tif", "tiff"}:
        if suffix == "jpeg":
            return "jpg"
        if suffix == "tif":
            return "tiff"
        return suffix

    return "jpg"


def _build_page_url(base_url: str, page_no: int, page_size: int = 50) -> str:
    parsed = urllib.parse.urlparse(base_url)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    query["pageNo"] = [str(page_no)]
    query["pageSize"] = [str(page_size)]
    new_query = urllib.parse.urlencode(query, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def download_deepdanbooru_source(base_urls: list[str], output_dir: Path, archive_db: Path, limit: int) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(archive_db)
    _ensure_archive(conn)

    downloaded = 0
    seen_on_run = 0

    try:
        for base_url in base_urls:
            page_no = 1
            while True:
                page_url = _build_page_url(base_url, page_no)
                print(f"[deepdanbooru-source] page {page_no}: {page_url}")
                html = _request_text(page_url)
                post_ids = _extract_post_ids(html)

                if not post_ids:
                    break

                for post_id in post_ids:
                    seen_on_run += 1
                    if limit > 0 and downloaded >= limit:
                        conn.commit()
                        return downloaded, seen_on_run

                    if _already_downloaded(conn, post_id):
                        continue

                    detail_url = f"https://sizebooru.com/Details/{post_id}"
                    detail_html = _request_text(detail_url)
                    tags = _parse_tags_from_detail(detail_html)
                    if not tags:
                        continue

                    picture_url = f"https://sizebooru.com/Picture/{post_id}"
                    data, content_type, final_url = _request_binary(picture_url)
                    ext = _ext_from_response(content_type, final_url)

                    digest = hashlib.sha1(data).hexdigest()[:16]
                    filename = f"sizebooru_{post_id}_{digest}.{ext}"
                    image_path = output_dir / filename
                    image_path.write_bytes(data)

                    # gallery-dl-compatible sidecar naming
                    (output_dir / f"{filename}.txt").write_text(" ".join(tags) + "\n", encoding="utf-8")
                    (output_dir / f"{filename}.json").write_text(
                        json.dumps(
                            {
                                "id": post_id,
                                "source": "sizebooru",
                                "detail_url": detail_url,
                                "picture_url": picture_url,
                                "resolved_url": final_url,
                                "content_type": content_type,
                                "tags": tags,
                            },
                            ensure_ascii=False,
                        )
                        + "\n",
                        encoding="utf-8",
                    )

                    _mark_downloaded(conn, post_id, filename)
                    downloaded += 1

                conn.commit()

                if not _has_next_page(html, page_no):
                    break

                page_no += 1
    finally:
        conn.close()

    return downloaded, seen_on_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download DeepDanbooru source images and tag sidecars.")
    parser.add_argument("--url", action="append", required=True, help="Sizebooru advanced search URL (repeatable)")
    parser.add_argument("--output-dir", required=True, help="Output directory for image files")
    parser.add_argument("--archive-db", required=True, help="SQLite archive DB path")
    parser.add_argument("--limit", type=int, default=0, help="Max images to download in this run (0 = unlimited)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    downloaded, visited = download_deepdanbooru_source(
        base_urls=args.url,
        output_dir=Path(args.output_dir),
        archive_db=Path(args.archive_db),
        limit=args.limit,
    )
    print(f"Downloaded {downloaded} new images from {visited} discovered posts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
