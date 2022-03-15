# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:45:07
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-15 23:40:46

from flask_login import login_required

from . import admin_api, csrf, db, main_api


@main_api.route("/profile/edit", methods=["POST"])
@login_required
@csrf.exempt
def edit_profile():
    pass
