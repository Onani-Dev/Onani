# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-24 02:05:16
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-04 00:21:07
from cgi import FieldStorage
from typing import Union

from flask import request
from flask_login import current_user
from Onani.forms import UploadForm
from Onani.models import Post, PostRating, Tag
from PIL import UnidentifiedImageError

from . import create_files, db


def upload_post(form: UploadForm) -> Union[Post, None]:
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
        (t.lower().strip().replace(" ", "_") if t else None)
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
