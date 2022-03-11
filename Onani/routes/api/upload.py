# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 02:46:35
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 03:22:27
from cgi import FieldStorage

from flask import request
from flask_login import (
    current_user,
    login_required,
)
from Onani.controllers import create_file
from Onani.models import File, Post, PostRating

from . import csrf, db, main_api, make_api_response


@main_api.route("/upload", methods=["POST"])
@login_required
@csrf.exempt
def file_upload():
    uploaded_file: FieldStorage = request.files["file"]
    if uploaded_file.filename:
        filetype = uploaded_file.mimetype.split("/")[1]
        if filetype not in ["jpeg", "jpg", "gif", "png", "webp", "jfif"]:
            raise ValueError("Invalid File type")

        # tags = []
        # # if request.form.get("tags"):
        # #     strings = request.form.get("tags").split(",")
        # #     tags = onaniDB.add_tags(tag_strings=parse_tags(strings))

        post = Post(
            source=request.form.get("source", ""),
            uploader=current_user.id,
            rating=PostRating(
                int(request.form.get("rating", 2))
                if int(request.form.get("rating", 2)) in {1, 2, 3}
                else 2
            ),
        )

        file = create_file(post, uploaded_file.read())

        db.session.add_all([file, post])
        db.session.commit()

        return make_api_response({"path": f"/post/{post.id}"})
    raise ValueError("File not given.")
