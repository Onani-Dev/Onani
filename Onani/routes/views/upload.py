# -*- coding: utf-8 -*-
from flask import current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from Onani.controllers.utils import flash_form_errors
from Onani.forms import UploadForm
from Onani.models import UserPermissions
from Onani.services.posts import upload_post
from PIL import UnidentifiedImageError

from . import db, main


@main.route("/upload/", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = request.files.getlist(form.file.name)[0]
        file_data = file.stream.read()
        can_create = current_user.has_permissions(UserPermissions.CREATE_TAGS)
        try:
            post = upload_post(
                file_data=file_data,
                original_filename=file.filename,
                tags_raw=form.tags.data,
                source=form.source.data,
                description=form.description.data,
                uploader=current_user,
                rating=form.rating.data,
                images_dir=current_app.config["IMAGES_DIR"],
                can_create_tags=can_create,
                tag_char_limit=current_app.config["TAG_CHAR_LIMIT"],
                post_min_tags=current_app.config["POST_MIN_TAGS"],
            )
            if post:
                return redirect(url_for("main.post_page", post_id=post.id))
        except UnidentifiedImageError:
            form.file.errors.append(
                f"The file {form.file.name} could not be read — ensure it is supported and not corrupted."
            )
        except ValueError as e:
            form.file.errors.append(str(e))
    flash_form_errors(form)
    return render_template("/routes/upload/index.jinja2", form=form)
