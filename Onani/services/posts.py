# -*- coding: utf-8 -*-
import contextlib
import io
import os
from html import escape
from typing import Iterable, List, Optional, Set, Tuple

from emoji import emojize
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from Onani import db
from Onani.controllers.utils import startswith_min
from Onani.models import (
    Post,
    PostComment,
    PostRating,
    Tag,
    TagType,
    User,
    UserPermissions,
)
from Onani.models.post import FileType
from PIL import UnidentifiedImageError

from .files import determine_meta_tags, get_file_data, get_video_data, detect_video_format, create_video_thumbnail, ensure_shard_dir, shard_path

_VIDEO_FORMATS = {"mp4", "webm", "mov", "avi", "mkv", "m4v"}

_CHAR_BLACKLIST = [chr(i) for i in range(32)]  # ASCII control characters 0–31


def format_tag(tag: str, tag_char_limit: int) -> Tuple[str, Optional[str]]:
    """Normalise a raw tag string into a canonical tag name.

    Returns:
        ``(canonical_name, warning_message)`` where ``warning_message`` is
        ``None`` on success or a human-readable description of why the tag
        was rejected.
    """
    tag = escape(tag.lower().strip())
    tag = "".join(c for c in tag if c not in _CHAR_BLACKLIST)

    if not tag:
        return "", None

    if len(tag) > tag_char_limit:
        return "", (
            f'Tag "{tag}" was not added — it exceeds the tag character limit'
            f" ({tag_char_limit})."
        )

    tag = tag.replace(" ", "_")
    return tag, None


def parse_tags(
    tags: Iterable[str],
    can_create_tags: bool,
    tag_char_limit: int,
) -> Set[Tag]:
    """Convert an iterable of raw tag strings into a set of ``Tag`` ORM objects.

    Args:
        tags: Raw tag strings (may include ``type:name`` prefixes).
        can_create_tags: Whether new tags may be created by the caller.
        tag_char_limit: Maximum allowed length for a single tag name.
    """
    taglist: Set[Tag] = set()

    for tag_str in tags:
        tag_str, _warning = format_tag(tag_str, tag_char_limit)
        if not tag_str:
            continue

        new_tag_type = None
        if ":" in tag_str:
            prefix, tag_no_prefix = tag_str.split(":", 1)
            prefix = prefix.strip()
            tag_no_prefix = tag_no_prefix.strip()

            for tag_type in TagType:
                if tag_type == TagType.BANNED:
                    continue
                if startswith_min(tag_type.name.lower(), prefix, min_len=3):
                    new_tag_type = tag_type
                    tag_str = tag_no_prefix
                    break

        if not tag_str:
            continue

        tag = Tag.query.filter_by(name=tag_str).first()

        if tag and new_tag_type and tag.type != new_tag_type:
            new_tag_name = f"{tag_str}_({new_tag_type.name.lower()})"
            tag = Tag.query.filter_by(name=new_tag_name).first()

            if not tag:
                if not can_create_tags:
                    continue
                tag = Tag(name=new_tag_name, post_count=0, type=new_tag_type)
                db.session.add(tag)
                try:
                    with db.session.begin_nested():
                        db.session.flush()
                except IntegrityError:
                    # Another worker created the same tag concurrently.
                    # begin_nested() rolls back only this savepoint, not the
                    # whole transaction.
                    tag = Tag.query.filter_by(name=new_tag_name).first()
                    if not tag:
                        continue

        if not tag:
            if not can_create_tags:
                continue
            tag = Tag(name=tag_str, post_count=0, type=new_tag_type)
            db.session.add(tag)
            try:
                with db.session.begin_nested():
                    db.session.flush()
            except IntegrityError:
                # Another worker created the same tag concurrently.
                tag = Tag.query.filter_by(name=tag_str).first()
                if not tag:
                    continue

        taglist.add(tag)

    return taglist


def set_tags(
    post: Post,
    tags: Set[str],
    old_tags: Set[str],
    can_create_tags: bool,
    tag_char_limit: int,
    post_min_tags: int,
) -> None:
    """Diff and apply a new tag set to a post, updating tag counts.

    Args:
        post: The post to update.
        tags: The new desired tag names.
        old_tags: The previous tag names (used to compute the diff).
        can_create_tags: Whether new tags may be created.
        tag_char_limit: Maximum tag name length from config.
        post_min_tags: Minimum required tags before ``meta:tag_request`` is added.
    """
    if not isinstance(tags, set):
        tags = set(tags)
    if not isinstance(old_tags, set):
        old_tags = set(old_tags or [])

    added_raw = tags.difference(old_tags)
    removed_raw = old_tags.difference(tags)

    removed = parse_tags(removed_raw, can_create_tags=can_create_tags, tag_char_limit=tag_char_limit)
    added = parse_tags(added_raw, can_create_tags=can_create_tags, tag_char_limit=tag_char_limit)

    post.tags.extend(added)

    for t in added:
        if t.explicit and post.rating != PostRating.EXPLICIT:
            post.rating = PostRating.EXPLICIT
        t.recount_posts()

    for t in removed:
        with contextlib.suppress(ValueError):
            post.tags.remove(t)
        t.recount_posts()

    # Apply meta tags based on post dimensions/size
    meta = determine_meta_tags(
        post.width,
        post.height,
        post.filesize,
        (post.filename or ".").split(".")[1],
        min_tags=post_min_tags,
        tag_count=post.tags.with_entities(func.count()).scalar() or len(tags),
    )
    post.tags.extend(parse_tags(meta, can_create_tags=True, tag_char_limit=tag_char_limit))

    current_tag_count = post.tags.with_entities(func.count()).scalar()
    if current_tag_count > post_min_tags:
        if tag_request := post.tags.filter_by(name="tag_request").first():
            post.tags.remove(tag_request)


def create_post(
    source: str,
    description: str,
    uploader: User,
    rating: str,
    image_file: io.BytesIO,
    filesize: int,
    hash_sha256: str,
    hash_md5: str,
    width: int,
    height: int,
    filename: str,
    file_type: str,
    original_filename: str,
    tags: Set[str],
    images_dir: str,
    can_create_tags: bool,
    tag_char_limit: int,
    post_min_tags: int,
    imported_from: str = None,
) -> Post:
    """Persist a new post (image + metadata) to the database and filesystem.

    Args:
        images_dir: Filesystem path where post images are stored (from config).
        can_create_tags: Whether the uploader may create new tags.
        tag_char_limit: Maximum tag name length from config.
        post_min_tags: Minimum required tag count from config.
    """
    post = Post()

    # Guard against duplicates before the object is associated with the
    # session (prevents autoflush from firing a poisoned INSERT later).
    # We re-check after the flush via IntegrityError to handle the concurrent
    # window between two workers both passing this pre-flight check.
    if Post.query.filter(
        (Post.sha256_hash == hash_sha256) | (Post.filename == filename)
    ).first():
        raise ValueError("Post already exists.")

    post.source = source
    post.description = description
    post.uploader = uploader
    post.rating = rating
    post.filename = filename
    post.md5_hash = hash_md5
    post.sha256_hash = hash_sha256
    post.width = width
    post.height = height
    post.filesize = filesize
    post.file_type = file_type
    post.type = FileType.VIDEO if file_type in _VIDEO_FORMATS else FileType.IMAGE
    post.original_filename = original_filename
    post.imported_from = imported_from

    # Add to session and flush to get a DB-assigned primary key BEFORE creating
    # any post_tags associations. Without this, SQLAlchemy's autoflush fires
    # inside set_tags() (triggered by Tag.query calls), tries to INSERT post_tags
    # referencing the new post_id, but PostgreSQL's immediate FK check fails
    # because the posts row isn't visible yet in the same flush batch.
    db.session.add(post)
    try:
        with db.session.begin_nested():
            db.session.flush()
    except IntegrityError:
        # Another worker inserted the same hash/filename between our pre-flight
        # check and this flush — treat it as a duplicate.
        raise ValueError("Post already exists.")

    set_tags(post, tags, set(), can_create_tags, tag_char_limit, post_min_tags)

    filepath = ensure_shard_dir(images_dir, filename)
    with open(filepath, "wb") as f:
        image_file.seek(0)
        f.write(image_file.read())

    # For videos, generate a JPEG thumbnail so nginx image_filter can serve it
    if file_type in _VIDEO_FORMATS:
        stem = filename.rsplit(".", 1)[0]
        thumb_name = f"{stem}.jpg"
        thumb_path = ensure_shard_dir(images_dir, thumb_name)
        create_video_thumbnail(filepath, thumb_path)

    uploader.post_count = uploader.posts.with_entities(func.count()).scalar()
    db.session.commit()

    return post


def upload_post(
    file_data: bytes,
    original_filename: str,
    tags_raw: str,
    source: str,
    description: str,
    uploader: User,
    rating: str,
    images_dir: str,
    can_create_tags: bool,
    tag_char_limit: int,
    post_min_tags: int,
) -> Post:
    """Parse raw uploaded bytes and create a post.

    Raises:
        UnidentifiedImageError: If the file cannot be read as an image.
        ValueError: If the file type is unsupported.
    """
    tags: Set[str] = set(tags_raw.split(" "))

    video_fmt = detect_video_format(file_data)
    if not video_fmt:
        # Check file extension as fallback
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        if ext in _VIDEO_FORMATS:
            video_fmt = ext

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

    return create_post(
        source,
        description,
        uploader,
        rating,
        image_file,
        filesize,
        hash_sha256,
        hash_md5,
        width,
        height,
        filename,
        file_type,
        original_filename,
        tags,
        images_dir,
        can_create_tags,
        tag_char_limit,
        post_min_tags,
    )


def create_comment(author: User, post: Post, content: str) -> PostComment:
    """Create and persist a comment on a post."""
    comment = PostComment()
    comment.author = author
    comment.post = post
    comment.content = emojize(content, language="alias")
    db.session.add(comment)
    db.session.commit()
    return comment
