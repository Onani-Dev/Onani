# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-31 23:58:51
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-04 03:39:26

import contextlib
import io
from typing import Iterable, List, Set

from emoji import emojize
from flask import current_app, flash, request
from flask_login import current_user
from Onani.controllers.utils import startswith_min
from Onani.forms import UploadForm
from Onani.models import Post, PostComment, PostRating, Tag, TagType, User
from PIL import UnidentifiedImageError
from sqlalchemy import func

from . import db
from .files import determine_meta_tags, get_file_data


def create_comment(author: User, post: Post, content: str) -> PostComment:
    """Create a comment on a post

    Args:
        author (User): The user to post the comment on behalf of
        post (Post): The post to comment on
        content (str): The comment's body

    Returns:
        PostComment: The post database object
    """
    comment = PostComment()
    comment.author = author
    comment.post = post
    comment.content = emojize(content, language="alias", use_aliases=True)

    db.session.add(comment)
    db.session.commit()

    return comment


def format_tag(tag: str) -> str:
    """Takes in a string and formats it to be a tag's name"""
    CHAR_BLACKLIST = [chr(i) for i in range(32)]  # ASCII char 0-31

    tag = tag.lower().strip()

    tag = "".join(c for c in tag if c not in CHAR_BLACKLIST)

    if not tag:
        return ""

    if len(tag) > current_app.config["TAG_CHAR_LIMIT"]:
        flash(
            f'Tag "{tag}" was not added due to it being over the tag character limit ({current_app.config["TAG_CHAR_LIMIT"]}).',
            "warning",
        )
        return ""

    tag = tag.replace(" ", "_")
    return tag


def parse_tags(tags: Iterable[str]) -> Set[Tag]:
    """Parses a list of tags for meta tags, and returns the let of tags to actually add to the post

    Args:
        tags (Iterable[str]): a list of the tags to parse

    Returns:
        Set[Tag]: The tags to add to the post
    """
    taglist = set()

    for tag_str in tags:
        # first we format the tag
        tag_str = format_tag(tag_str)
        if not tag_str:
            # empty tag OR invalid tag
            continue

        # We handle special tags
        new_tag_type = None
        if ":" in tag_str:
            prefix, tag_no_prefix = tag_str.split(":", 1)
            prefix = prefix.strip()
            tag_no_prefix = tag_no_prefix.strip()

            # We check for types
            for type in TagType:
                if type == TagType.BANNED:  # You can't make a tag "BANNED"
                    continue
                if startswith_min(
                    type.name.lower(), prefix, min_len=3
                ):  # We don't want 1-2 char bc ambiguous
                    # make the tag 'tag' of type 'type'
                    new_tag_type = type
                    tag_str = tag_no_prefix
                    break

        # Check if the tag exists and make it if not
        if tag_str:  # Musn't be empty (can happen with 'char:' for exemple)
            tag = Tag.query.filter_by(name=tag_str).first()

            if tag and new_tag_type and tag.type != new_tag_type:
                # The modified tag name to deal with name conflicts
                new_tag_name = f"{tag_str}_({new_tag_type.name.lower()})"

                # Find if it already exists
                tag = Tag.query.filter_by(name=new_tag_name).first()

                # create it if it doesnt exist
                if not tag:
                    tag = Tag(name=new_tag_name, post_count=0, type=new_tag_type)

            if not tag:
                # make it and add it to the session
                tag = Tag(name=tag_str, post_count=0)
                db.session.add(tag)

            taglist.add(tag)

    return taglist


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
    orginal_filename: str,
    tags: Set[str],
) -> Post:
    """Standardized way to create a post on Onani. You must handle commiting to database outside of this, as it does not automatically commit.

    Args:
        source (str): Post's source
        description (str): The description for the post
        uploader (User): The user to upload this post under
        rating (str): The string rating for this post
        image_file (io.BytesIO): The file data in BytesIO object
        filesize (int): The filesize integer
        hash_sha256 (str): The sha256 hash for the file on disk
        hash_md5 (str): The md5 hash for the file on disk
        width (int): The width of the image
        height (int): The height of the image
        filename (str): The filename for the file on disk  (<sha256>.<file_type>)
        file_type (str): The file extension type of the file
        orginal_filename (str): The original name of the uploaded file
        tags (Set[str]): The tags in string form

    Returns:
        Post: The created post, ready to be commited.
    """
    # Create the post
    post = Post()

    # Add all post info to the post object
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
    post.original_filename = orginal_filename

    # Set the post's tags
    set_tags(post, tags)

    # write to file
    with open(f"/images/{filename}", "wb") as f:
        image_file.seek(0)
        f.write(image_file.read())

    return post


def upload_post(form: UploadForm):
    # Get the file
    file = request.files.getlist(form.file.name)[0]

    # Turn the file into bytes.
    file_data = file.stream.read()

    # Split and Delete duplicate tags
    tags: Set[str] = set(form.tags.data.split(" "))

    # Get metadata from the file
    try:
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
    except UnidentifiedImageError as e:
        form.file.errors.append(
            f"The file {form.file.name} could not be read, Please ensure it is supported and not corrupted/broken."
        )
    except ValueError as e:
        form.file.errors.append(str(e))
    else:

        post = create_post(
            form.source.data,
            form.description.data,
            current_user,
            form.rating.data,
            image_file,
            filesize,
            hash_sha256,
            hash_md5,
            width,
            height,
            filename,
            file_type,
            file.filename,
            tags,
        )

        # increase the user's post count
        current_user.post_count = current_user.posts.with_entities(
            func.count()
        ).scalar()

        # Add post to session
        db.session.add(post)

        # commit the data to the database
        db.session.commit()

        return post


def set_tags(post: Post, tags: Set[str], old_tags: Set[str] = None):
    """Set a posts tags

    Args:
        post (Post): _description_
        tags (Set[str]): _description_
        old_tags (Set[str], optional): _description_. Defaults to None.
    """
    # We do a little slopping
    if not isinstance(tags, set):
        tags = set(tags)

    if not isinstance(old_tags, (set, None)):
        old_tags = set(old_tags)

    added_tags = tags.difference(old_tags or set())

    removed_tags = (
        old_tags.difference(tags) if old_tags else set()
    )  # Tags in "old_tags" but not in "tags"
    # tags that are in both are ignored as they were not edited

    # meta tags in removed_tags shouldn't be applied, but we need to parse so it can't really be avoided
    removed_tags = parse_tags(removed_tags)

    # added_tags might contain meta tags, so we parse for those
    added_tags = parse_tags(added_tags)

    post.tags.extend(added_tags)

    for t in added_tags:
        # Add the explicit rating if the tag is explicit
        if t.explicit and post.rating != PostRating.EXPLICIT:
            post.rating = PostRating.EXPLICIT
        # Make the tags post_count go up.
        t.post_count += 1

    # it'd be easier to remove if post.tags was a set but whatever
    for t in removed_tags:
        with contextlib.suppress(ValueError):
            post.tags.remove(t)
        # It has less posts now ;)
        t.post_count -= 1

    # Redetermine the meta tags
    post.tags.extend(
        parse_tags(
            determine_meta_tags(
                post.width,
                post.height,
                post.filesize,
                (post.filename or "").split(".")[1],
                post.tags.with_entities(func.count()).scalar() or len(tags),
            )
        )
    )

    # Remove the tag request if the amount of tags is over the minimum
    if (
        post.tags.with_entities(func.count()).scalar()
        > current_app.config["POST_MIN_TAGS"]
    ):
        if tag_request := post.tags.filter_by(name="tag_request").first():
            post.tags.remove(tag_request)
