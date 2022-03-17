# -*- coding: utf-8 -*-
# @Author: dirt3009
# @Date:   2022-03-17 20:38:10
# @Last Modified by:   dirt3009
# @Last Modified time: 2022-03-17 21:18:08

import datetime

from flask import jsonify, request
from flask_login import current_user
from Onani.controllers import role_required
from Onani.models import UserRoles

from . import admin_api, db
from .. import make_api_response

@admin_api.route("/news", methods=["POST"])
@role_required(role=UserRoles.ADMIN)
def create_article():
    data = request.json
    uploader = db.Column(db.Integer, current_user.id)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    title = db.Column(db.String, data["title"])
    content = db.Column(db.UnicodeText, data["content"])
    db.session.commit()
    return make_api_response()
