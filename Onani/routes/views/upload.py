# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-10 22:13:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-24 02:10:35
from cgi import FieldStorage

from flask import redirect, render_template, request
from flask_login import login_required
from Onani.controllers import upload_files
from Onani.forms import UploadForm

from . import db, main


@main.route("/upload/", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm(request.form)
    if request.method == "POST" and form.validate():
        if post := upload_files(form):
            return redirect(f"/posts/{post.id}")

    return render_template("/upload.jinja2", form=form)
