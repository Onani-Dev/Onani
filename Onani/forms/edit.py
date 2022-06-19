# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-06-19 08:18:30
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-19 09:30:53
from flask_wtf import FlaskForm
from Onani.models import PostRating
from wtforms import SelectField, StringField, HiddenField
from wtforms.widgets import TextArea


class EditForm(FlaskForm):
    parent = StringField(
        "Parent ID",
        render_kw={
            "placeholder": "Parent #ID",
            "id": "post-edit-parent",
        },
    )

    rating = SelectField(
        "Rating",
        render_kw={
            "id": "post-edit-rating",
        },
        choices=PostRating.choices(),
        coerce=PostRating.coerce,
    )

    source = StringField(
        "Source",
        render_kw={
            "placeholder": "The source for this post.",
            "id": "post-edit-source",
        },
    )

    description = StringField(
        "Description",
        render_kw={
            "placeholder": "The description for this post.",
            "id": "post-edit-desc",
        },
        widget=TextArea(),
    )

    tags = StringField(
        "Tags",
        render_kw={
            "placeholder": "The tags for this post (Split with spaces)",
            "id": "post-edit-tags",
            "spellcheck": "false",
        },
        widget=TextArea(),
    )

    old_tags = HiddenField(
        "Old Tags",
        render_kw={"id": "post-edit-old-tags"},
    )
