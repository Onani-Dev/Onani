# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-18 21:46:25

from flask import abort, render_template, request
from flask_login import current_user, login_required
from Onani.models import NewsPost, NewsPostSchema

from . import main


@main.route("/news/")
@main.route("/news/<article_id>")
@login_required
def news(article_id=None):
    if not article_id:
        page = request.args.get("p", "0")

        # Convert the page to an int if it is a digit, if it is not, default to 0
        page = int(page) if page.isdigit() else 0
        news = NewsPost.query.order_by(NewsPost.id.desc()).paginate(
            per_page=10, page=page, error_out=False
        )

        return render_template("/news.jinja2", news=news)

    # Check if it is a valid number
    if not article_id.isdigit():
        # abort, it's not a number
        abort(404)

    # Convert to integer
    article_id = int(article_id)

    article = NewsPost.query.filter_by(id=article_id).first_or_404()

    page = request.args.get("p", "0")
    page = int(page) if page.isdigit() else 0

    # Render the user page
    return render_template(
        "/news_article.jinja2",
        article=article,
    )
