# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-10 22:13:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:47:36
from flask import redirect, render_template, url_for
from flask_login import login_required
from Onani.controllers import upload_post
from Onani.forms import UploadForm

from . import db, main


@main.route("/upload/", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        if post := upload_post(form):
            return redirect(url_for("main.post_index", post_id=post.id))

    return render_template("/routes/upload/index.jinja2", form=form)
