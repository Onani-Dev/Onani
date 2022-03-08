# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 03:28:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 04:14:52
from Onani.controllers import permissions_required
from Onani.models import UserPermissions

from . import admin


@admin.route("/")
@permissions_required(permissions=UserPermissions.MODERATOR)
def index():
    return "wow admin"
