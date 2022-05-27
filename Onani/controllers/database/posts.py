# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-31 23:58:51
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 22:49:58

from typing import Iterable, List, Set

from emoji import emojize
from flask import request
from flask_login import current_user
from Onani.controllers.utils import startswith_min
from Onani.forms import UploadForm
from Onani.models import Post, PostComment, PostRating, Tag, TagType, User
from PIL import UnidentifiedImageError
from sqlalchemy import func

from . import create_files, db


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

    if len(tag) > 64:
        # Maybe display a warning to the user?
        return ""

    tag = tag.replace(" ", "_")
    return tag


def parse_tags(post: Post, tags: Iterable[str]) -> List[Tag]:
    """Parses a list of tags for meta tags, and returns the list of tags to actually add to the post

    Args:
        post (Post): The post that the tags will be added to (used by meta tags)
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
            # Checks for meta tags
            if prefix == "pool" or startswith_min("collection", prefix, 3):
                # TODO: Add the post to the pool
                continue  # don't add the tag to the post

            if startswith_min("source", prefix, 3):
                # TODO: add source validation
                post.source = tag_no_prefix
                continue  # don't add the tag to the post

            # TODO: implement rating metatag

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

        # /!\ We should only reach here if the tag is not a metatag
        # that shouldn't be added to the post

        # Check if the tag exists and make it if not
        if tag_str:  # Musn't be empty (can happen with 'char:' for exemple)
            tag = Tag.query.filter_by(name=tag_str).first()
            if not tag:
                # make it and add it to the session
                tag = Tag(name=tag_str, post_count=0)
                db.session.add(tag)

            if new_tag_type is not None:
                tag.type = new_tag_type

            taglist.append(tag)

    return taglist


def upload_post(form: UploadForm):
    # Create the post
    post = Post()

    post.source = form.source.data
    post.description = form.description.data
    post.uploader = current_user
    post.rating = form.rating.data

    # Get the files
    files = request.files.getlist(form.files.name)

    # Turn the files into bytes.
    datas = (f.stream.read() for f in files)

    # Split and Delete duplicate tags
    tags = set(form.tags.data.split(" "))

    # save the files and add them to the post
    try:
        files, meta_tags = create_files(post, datas)
        tags.update(meta_tags)
        # Add tagme tag for posts with less than 10 tags
        if len(tags) <= 10:
            tags.add("meta:tagme")
    except UnidentifiedImageError as e:
        form.files.errors.append("Image file could not be opened.")
    except ValueError as e:
        form.files.errors.append(str(e))
    else:
        tags = parse_tags(post, tags)
        for t in tags:
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

        # Add post to session
        db.session.add(post)

        # commit the data to the database
        db.session.commit()

        return post
