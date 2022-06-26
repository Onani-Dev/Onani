# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-31 23:58:51
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-26 10:57:50

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


def parse_tags(tags: Iterable[str]) -> List[Tag]:
    """Parses a list of tags for meta tags, and returns the list of tags to actually add to the post

    Args:
        tags (Iterable[str]): a list of the tags to parse

    Returns:
        List[Tag]: The tags to add to the post
    """
    taglist = []

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

            taglist.append(tag)

    return taglist


def upload_post(form: UploadForm):
    # Create the post
    post = Post()

    post.source = form.source.data
    post.description = form.description.data
    post.uploader = current_user
    post.rating = form.rating.data

    # Get the file
    file = request.files.getlist(form.file.name)[0]

    # Turn the file into bytes.
    file_data = file.stream.read()

    # Split and Delete duplicate tags
    tags: set[str] = set(form.tags.data.split(" "))

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
        # Get meta tags based off of this shit idfk
        tags.update(determine_meta_tags(width, height, filesize, file_type, len(tags)))

        # Then turn all those strings into actual tags
        parsed_tags = parse_tags(tags)

        for t in parsed_tags:
            # add the tag to the post
            post.tags.append(t)

            if t.explicit:
                post.rating = PostRating.EXPLICIT

            # Increase the tag's post count
            t.post_count += 1

        # increase the user's post count
        current_user.post_count = current_user.posts.with_entities(
            func.count()
        ).scalar()

        # Add all post info to the post object
        post.filename = filename
        post.md5_hash = hash_md5
        post.sha256_hash = hash_sha256
        post.width = width
        post.height = height
        post.filesize = filesize

        # write to file
        with open(f"/images/{filename}", "wb") as f:
            image_file.seek(0)
            f.write(image_file.read())

        # Add post to session
        db.session.add(post)

        # commit the data to the database
        db.session.commit()

        return post
