# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-18 23:56:36
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-19 00:51:32

from Onani.controllers import role_required
from Onani.models import UserRoles, Error
import flask
from sqlalchemy import desc

from . import admin


@admin.route("/error")
@role_required(role=UserRoles.MODERATOR)
def error_index():
    # Slow query but it's not like that endpoint will be the most used anyway
    errors = Error.query.order_by(desc(Error.created_at)).limit(10)
    return "<br><br>".join(
        f"<a href={flask.url_for('admin.error_view', error_id=e.id)}>{e.id}</a>"
        for e in errors
    )


@admin.route("/error/<error_id>")
@role_required(role=UserRoles.MODERATOR)
def error_view(error_id):
    error: Error = Error.query.filter_by(id=error_id).first_or_404(
        "There is no error with that ID"
    )
    return f"""Error <strong>{error.id}</strong>
<hr>
<pre><code>
{flask.Markup.escape(error.traceback)}
</pre></code>"""
