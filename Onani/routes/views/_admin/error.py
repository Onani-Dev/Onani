# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-18 23:56:36
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:58:52

from flask import current_app, render_template, request
from Onani.controllers import permissions_required, role_required
from Onani.controllers.utils import get_page
from Onani.models import Error, UserRoles
from Onani.models.user.permissions import UserPermissions

from . import admin


@admin.route("/errors/")
@role_required(role=UserRoles.MODERATOR)
@permissions_required(permissions=UserPermissions.VIEW_LOGS)
def error_index():
    # Get the page
    page = get_page()

    # Slow query but it's not like that endpoint will be the most used anyway
    errors = Error.query.order_by(Error.created_at.desc()).paginate(
        per_page=current_app.config["PER_PAGE_ERRORS"], page=page, error_out=False
    )
    return render_template("/admin/errors/index.jinja2", errors=errors)


@admin.route("/errors/<error_id>/")
@role_required(role=UserRoles.MODERATOR)
@permissions_required(permissions=UserPermissions.VIEW_LOGS)
def error_view(error_id):
    error: Error = Error.query.filter_by(id=error_id).first_or_404(
        "There is no error with that ID"
    )
    return render_template("/admin/errors/error.jinja2", error=error)
