#!/usr/bin/env python3
"""Prepare a DeepDanbooru-friendly manifest from gallery-dl output.

Expected input layout:
- image files downloaded by gallery-dl
- sidecar tag files produced by --write-tags (same basename, .txt extension)

Outputs:
- train.txt     : <relative_image_path>\t<tag1 tag2 ...>
- dataset.jsonl : one JSON object per image
- tags.txt      : unique tags sorted by descending frequency
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


def _split_tag_line(line: str) -> list[str]:
    line = line.strip()
    if not line:
        return []
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
    else:
        parts = line.split()
    return [p for p in parts if p]


def _normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "_")


def _load_tags(tag_file: Path) -> list[str]:
    raw = tag_file.read_text(encoding="utf-8", errors="ignore")
    tags: list[str] = []
    for line in raw.splitlines():
        tags.extend(_split_tag_line(line))

    seen = set()
    deduped: list[str] = []
    for tag in tags:
        norm = _normalize_tag(tag)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        deduped.append(norm)
    return deduped


def build_dataset(input_dir: Path, output_dir: Path, min_tags: int) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.txt"
    jsonl_path = output_dir / "dataset.jsonl"
    tags_path = output_dir / "tags.txt"

    records: list[tuple[Path, list[str]]] = []
    tag_counter: Counter[str] = Counter()

    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue

        sidecar_txt = Path(str(path) + ".txt")
        fallback_txt = path.with_suffix(".txt")
        tag_file = sidecar_txt if sidecar_txt.exists() else fallback_txt
        if not tag_file.exists():
            continue

        tags = _load_tags(tag_file)
        if len(tags) < min_tags:
            continue

        records.append((path, tags))
        tag_counter.update(tags)

    with train_path.open("w", encoding="utf-8") as train_f, jsonl_path.open("w", encoding="utf-8") as jsonl_f:
        for image_path, tags in records:
            rel = image_path.relative_to(input_dir).as_posix()
            train_f.write(f"{rel}\t{' '.join(tags)}\n")
            jsonl_f.write(json.dumps({"file": rel, "tags": tags}, ensure_ascii=False) + "\n")

    sorted_tags = sorted(tag_counter.items(), key=lambda item: (-item[1], item[0]))
    with tags_path.open("w", encoding="utf-8") as tags_f:
        for tag, _count in sorted_tags:
            tags_f.write(tag + "\n")

    return len(records), len(sorted_tags)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DeepDanbooru training files from gallery-dl downloads.")
    parser.add_argument("--input-dir", required=True, help="Directory where gallery-dl downloaded images + sidecars.")
    parser.add_argument("--output-dir", required=True, help="Directory to write train.txt, dataset.jsonl, tags.txt.")
    parser.add_argument("--min-tags", type=int, default=1, help="Drop samples with fewer than this many tags.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count, vocab = build_dataset(Path(args.input_dir), Path(args.output_dir), args.min_tags)
    print(f"Wrote {count} samples with {vocab} unique tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
