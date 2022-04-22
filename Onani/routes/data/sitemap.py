# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-23 02:24:06
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-23 02:31:46
from urllib.parse import urlparse

from flask import current_app, make_response, render_template, request
from Onani.models import Post

from . import db, main


@main.route("/sitemap")
@main.route("/sitemap/")
@main.route("/sitemap.xml")
def sitemap():
    """
    Route to dynamically generate a sitemap of your website/application.
    lastmod and priority tags omitted on static pages.
    lastmod included on dynamic content such as blog posts.
    """

    host_components = urlparse(request.host_url)
    host_base = f"{host_components.scheme}://{host_components.netloc}"

    # Static routes with static content
    static_urls = []
    for rule in current_app.url_map.iter_rules():
        if (
            not str(rule).startswith("/admin")
            and not str(rule).startswith("/user")
            and not str(rule).startswith("/api")
            and "GET" in rule.methods
            and len(rule.arguments) == 0
        ):
            url = {"loc": f"{host_base}{str(rule)}"}
            static_urls.append(url)

    # Dynamic routes with dynamic content
    dynamic_urls = []
    posts = Post.query.all()
    for post in posts:
        url = {
            "loc": f"{host_base}/posts/{post.id}",
            "lastmod": post.uploaded_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        dynamic_urls.append(url)

    xml_sitemap = render_template(
        "public/sitemap.xml",
        static_urls=static_urls,
        dynamic_urls=dynamic_urls,
        host_base=host_base,
    )
    response = make_response(xml_sitemap)
    response.headers["Content-Type"] = "application/xml"

    return response
