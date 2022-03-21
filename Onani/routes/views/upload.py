# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-10 22:13:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-21 18:23:01
from cgi import FieldStorage

from flask import redirect, render_template, request
from flask_login import current_user, login_required
from Onani.controllers import create_files
from Onani.forms import UploadForm
from Onani.models import File, Post, PostRating, Tag, User, UserSettings
from PIL import UnidentifiedImageError
from psycopg2.errors import UniqueViolation

from . import db, main


@main.route("/upload/", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm(request.form)
    if request.method == "POST" and form.validate():
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

                # Increase the tag's post count
                tag.post_count += 1

        # save the files and add them to the post
        try:
            create_files(post, datas)
        except UnidentifiedImageError as e:
            form.files.errors.append("Image file could not be opened.")
        except ValueError as e:
            form.files.errors.append(str(e))
        else:
            # increase the user's post count
            current_user.post_count = len(current_user.posts.all())

            # Add post to session
            db.session.add(post)

            # commit the data to the database
            db.session.commit()

            # redirect to the post
            return redirect(f"/posts/{post.id}")

    return render_template("/upload.jinja2", form=form)
