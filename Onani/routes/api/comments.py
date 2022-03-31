# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-01 02:10:13
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-01 02:20:15

from flask_login import login_required

from . import admin_api, csrf, db, main_api


@main_api.route("/comment/post", methods=["POST"])
@login_required
@csrf.exempt
def comment_post():
    raise NotImplementedError()
