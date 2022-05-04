# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:55:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:56:25

from flask import abort, render_template, request, current_app
from flask_login import current_user, login_required
from Onani.models import NewsPost, NewsPostSchema, User
from Onani.controllers.utils import get_page
from . import main


@main.route("/news/")
@main.route("/news/<article_id>")
def get_news(article_id=None):
    if not article_id:
        page = get_page()
        news = NewsPost.query.order_by(NewsPost.id.desc()).paginate(
            per_page=current_app.config["PER_PAGE_NEWS"], page=page, error_out=False
        )

        return render_template("/routes/news/index.jinja2", news=news)

    article_id = int(article_id) if article_id.isdigit() else abort(404)

    article = NewsPost.query.filter_by(id=article_id).first_or_404()

    # Render the user page
    return render_template("/routes/news/news.jinja2", article=article)
