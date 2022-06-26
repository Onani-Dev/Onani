# -*- coding: utf-8 -*-
# @Author: dirt3009
# @Date:   2022-03-09 03:00:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-26 15:23:49

from flask import abort, current_app, render_template, request
from flask_login import current_user
from Onani.controllers.utils import get_page
from Onani.forms import EditForm
from Onani.models import Collection
from sqlalchemy import distinct, func

from . import main


@main.route("/collections")
def collections_index():
    return render_template(
        "/routes/collections/index.jinja2", collections=Collection.query.all()
    )
