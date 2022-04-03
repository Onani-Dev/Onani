# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-31 23:58:51
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-03 14:51:11

from cgi import FieldStorage
from typing import List

from flask import request
from flask_login import current_user
from Onani.forms import UploadForm
from Onani.models import Post, PostComment, PostRating, Tag, User
from PIL import UnidentifiedImageError

from . import create_files, db
from Onani.controllers.utils import startswith_min


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
    comment.content = content

    db.session.add(comment)
    db.session.commit()

    return comment


def format_tag(tag: str) -> str:
    """Takes in a string and formats it to be a tag's name"""
    tag = tag.lower().strip()
    if not tag:
        return ''

    if 32 < len(tag):
        # Maybe display a warning to the user?
        return ''

    tag = tag.replace(" ", "_")
    return tag


def parse_tags(post: Post, tags: List[str]) -> List[Tag]:
    """Parses a list of tags, and returns the list of tags to actually add to the post

    Args:
        post (Post): The post that the tags will be added to (used by meta tags)
        tags (List[str]): a list of the tags to parse

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
        if ':' in tag_str: 
            prefix, tag_no_prefix = tag_str.split(':', 1)
            # Checks for meta tags
            if prefix == 'pool' or startswith_min('collection', prefix, 3):
                # TODO: Add the post to the pool
                continue # don't add the tag to the post

            if startswith_min('source', prefix, 3):
                # TODO: add source validation
                post.source = tag_no_prefix
                continue # don't add the tag to the post
            
            # We check for types
            for type in TagType:
                if type == TagType.BANNED: # You can't make a tag "BANNED"
                    continue
                if startswith_min(type.name.lower(), prefix, min_len=3): # We don't want 1-2 char bc ambiguous
                    # make the tag 'tag' of type 'type'
                    new_tag_type = type
                    break

        # /!\ We should only reach here if the tag is not a metatag
        # that shouldn't be added to the post

        # Check if the tag exists and make it if not
        tag = Tag.query.filter_by(name=tag_str).first()
        if not tag:
            # make it and add it to the session
            tag = Tag(name=t, post_count=0)
            db.session.add(tag)

        if new_tag_type is not None:
            tag.type = new_tag_type
        
        taglist.append(tag)
            
    db.session.commit()
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

    # Delete duplicate tags and replace spaces with underscores + split the tags
    tags = {
        (t.lower().strip().replace(" ", "_") if t and len(t) < 32 else None)
        for t in form.tags.data.split(",")
    }

    # save the files and add them to the post
    try:
        files, meta_tags = create_files(post, datas)
        tags.update(meta_tags)
    except UnidentifiedImageError as e:
        form.files.errors.append("Image file could not be opened.")
    except ValueError as e:
        form.files.errors.append(str(e))
    else:
        for t in tags:
            if t:
                # Check if the tag exists
                tag = Tag.query.filter_by(name=t).first()
                if not tag:
                    # make it and add it to the session
                    tag = Tag(name=t, post_count=0)
                    db.session.add(tag)

                # add the tag to the post
                post.tags.append(tag)

                if tag.explicit:
                    post.rating = PostRating.EXPLICIT

                # Increase the tag's post count
                tag.post_count += 1

        # increase the user's post count
        current_user.post_count = len(current_user.posts.all())

        # Add post to session
        db.session.add(post)

        # commit the data to the database
        db.session.commit()

        return post
