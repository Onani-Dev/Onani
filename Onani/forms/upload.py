# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:02:11
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-22 03:20:17

from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired
from Onani.models import PostRating
from wtforms import MultipleFileField, SelectField, StringField, SubmitField
from wtforms.validators import URL, DataRequired, Length, Optional
from wtforms.widgets import TextArea


class UploadForm(FlaskForm):
    files = MultipleFileField(
        "Files",
        render_kw={
            "id": "file-upload",
            "accept": "image/gif, image/jpeg, image/png, image/tiff, image/bmp, image/webp",
            # "onchange": "displayImage(this)",
            "class": "uploader-input",
        },
        validators=[
            FileAllowed(
                [
                    "jpeg",
                    "jpg",
                    "gif",
                    "png",
                    "webp",
                    "jfif",
                    "pjpeg",
                    "pjp",
                    "tiff",
                    "webp",
                ],
                "Image Files only.",
            ),
        ],
    )

    rating = SelectField(
        "Rating",
        render_kw={"placeholder": "The rating for this post"},
        choices=PostRating.choices(),
        coerce=PostRating.coerce,
        validators=[DataRequired()],
    )

    source = StringField(
        "Source",
        render_kw={
            "placeholder": "The source for this post/files.",
            "id": "file-source",
            "class": "uploader-input",
        },
        validators=[Optional(), URL(message="Must be a valid URL.")],
    )

    description = StringField(
        "Description",
        render_kw={
            "placeholder": "The description for this post.",
            "class": "uploader-textarea",
        },
        validators=[Optional(), Length(max=1024)],
        widget=TextArea(),
    )

    tags = StringField(
        "Tags",
        render_kw={
            "placeholder": "Add the tags for this post (Split with spaces)",
            "id": "file-tags",
            "class": "uploader-textarea",
        },
        validators=[Optional()],
        widget=TextArea(),
    )

    recaptcha = RecaptchaField()

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Upload",
            "id": "upload-button",
        },
    )
