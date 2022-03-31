# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-10 22:13:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-01 01:02:28
from cgi import FieldStorage

from flask import redirect, render_template, request
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
            return redirect(f"/posts/{post.id}")

    return render_template("/upload.jinja2", form=form)
