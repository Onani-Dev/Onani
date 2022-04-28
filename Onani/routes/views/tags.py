# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-27 19:17:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-27 20:08:22

import html

from flask import abort, render_template, request, current_app
from flask_login import current_user
from Onani.forms import AccountPlatformForm, AccountProfileForm, AccountSettingsForm
from Onani.models import Tag

from . import main


@main.route("/tags/")
@main.route("/tags/<tag_id>")
# @login_required
def tags(tag_id=None):
    if not tag_id:
        page = request.args.get("p", "0")
        sort = request.args.get("sort", "posts")

        match sort.lower():
            case "name":
                tags = Tag.query.order_by(Tag.name)
            case "type":
                tags = Tag.query.order_by(Tag.type.desc())
            case "posts":
                tags = Tag.query.order_by(Tag.post_count.desc())
            case _:
                tags = Tag.query.order_by(Tag.id)

        # Convert the page to an int if it is a digit, if it is not, default to 0
        page = int(page) if page.isdigit() else 0
        tags = tags.paginate(
            per_page=current_app.config["PER_PAGE_TAGS"], page=page, error_out=False
        )

        return render_template(
            "/tags.jinja2",
            tags=tags,
        )

    # Check if it is a valid number
    if not tag_id.isdigit():
        # abort, it's not a number
        abort(404)

    # Convert to integer
    tag_id = int(tag_id)

    tag = Tag.query.filter_by(id=tag_id).first_or_404()

    # Render the user page
    return render_template("/tag.jinja2", tag=tag)
