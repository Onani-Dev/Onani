#!/usr/bin/env python3
"""Build DeepDanbooru dataset structure (images + sqlite) from raw sidecars.

Input: a directory containing images and .txt sidecars (gallery-dl style).
Output:
- <output-dir>/images/<md5[:2]>/<md5>.<ext>
- <output-dir>/<database-name> (SQLite with posts table)
- <output-dir>/tags.txt (newline separated)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def _split_tags(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    if "," in raw:
        parts = [x.strip() for x in raw.split(",")]
    else:
        parts = raw.split()
    return [p for p in parts if p]


def _normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "_")


def _load_tags(sidecar: Path) -> list[str]:
    text = sidecar.read_text(encoding="utf-8", errors="ignore")
    tags: list[str] = []
    for line in text.splitlines():
        tags.extend(_split_tags(line))

    deduped: list[str] = []
    seen = set()
    for t in tags:
        n = _normalize_tag(t)
        if not n or n in seen:
            continue
        seen.add(n)
        deduped.append(n)
    return deduped


def _hash_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _create_db(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS posts")
    conn.execute(
        """
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            md5 TEXT NOT NULL,
            file_ext TEXT NOT NULL,
            tag_string TEXT NOT NULL,
            tag_count_general INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def _write_tags(path: Path, tag_counter: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for tag, _ in sorted(tag_counter.items(), key=lambda x: (-x[1], x[0])):
            f.write(tag + "\n")


def build_dataset(
    input_dir: Path,
    output_dir: Path,
    db_name: str,
    min_tags: int,
    tags_output: Path | None,
    clean_output: bool,
) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    images_root = output_dir / "images"

    db_path = output_dir / db_name

    if clean_output:
        if images_root.exists():
            shutil.rmtree(images_root)
        if db_path.exists():
            db_path.unlink()

    images_root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    _create_db(conn)

    tag_counter: Counter[str] = Counter()
    post_id = 1

    try:
        for image in sorted(input_dir.rglob("*")):
            if not image.is_file() or image.suffix.lower() not in IMAGE_EXTS:
                continue

            sidecar_txt = Path(str(image) + ".txt")
            fallback_txt = image.with_suffix(".txt")
            tag_file = sidecar_txt if sidecar_txt.exists() else fallback_txt
            if not tag_file.exists():
                continue

            tags = _load_tags(tag_file)
            if len(tags) < min_tags:
                continue

            md5 = _hash_file(image)
            file_ext = image.suffix.lower().lstrip(".")
            if file_ext == "jpeg":
                file_ext = "jpg"
            if file_ext == "tif":
                file_ext = "tiff"

            dst_dir = images_root / md5[:2]
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f"{md5}.{file_ext}"
            if not dst.exists():
                try:
                    os.link(image, dst)
                except OSError:
                    shutil.copy2(image, dst)

            tag_string = " ".join(tags)
            conn.execute(
                "INSERT INTO posts(id, md5, file_ext, tag_string, tag_count_general) VALUES(?,?,?,?,?)",
                (post_id, md5, file_ext, tag_string, len(tags)),
            )
            post_id += 1
            tag_counter.update(tags)

        conn.commit()
    finally:
        conn.close()

    if tags_output is not None:
        _write_tags(tags_output, tag_counter)

    return post_id - 1, len(tag_counter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DeepDanbooru sqlite/images dataset from raw downloads")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--db-name",
        "--database-name",
        dest="db_name",
        default="dataset.sqlite",
        help="SQLite filename (default: dataset.sqlite)",
    )
    parser.add_argument("--min-tags", type=int, default=10, help="Minimum tag count per image (default: 10)")
    parser.add_argument("--tags-output", default="", help="Optional path for tags.txt output")
    parser.add_argument(
        "--clean",
        "--clean-output",
        dest="clean_output",
        action="store_true",
        help="Remove output-dir before building",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tags_output = Path(args.tags_output) if args.tags_output else None
    samples, vocab = build_dataset(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        db_name=args.db_name,
        min_tags=args.min_tags,
        tags_output=tags_output,
        clean_output=args.clean_output,
    )
    print(f"Built dataset with {samples} posts and {vocab} unique tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
