# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-23 16:12:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 10:32:57

from feedgen.feed import FeedGenerator
from Onani.models.post import Post

from . import feed, make_feed_generator
from flask import url_for, request
from mimetypes import guess_type


@feed("/posts")
def posts() -> FeedGenerator:
    fg = make_feed_generator()

    fg.id("onani.feed.posts")
    fg.title("Onani posts")
    fg.subtitle("The latest Onani posts")
    fg.link(href=url_for("main.post_index", _external=True), rel="alternate")

    for p in reversed(Post.query.order_by(Post.id.desc()).limit(10).all()):
        p: Post
        fe = fg.add_entry()
        fe.id(f"onani.feed.posts.{p.id}")
        fe.title(p.title)
        fe.link(
            href=url_for("main.post_page", post_id=p.id, _external=True),
            rel="alternate",
        )
        # We need to do both, one for atom and one for RSS
        fe.author({"name": p.uploader.username})
        fe.author({"email": p.uploader.username})

        fe.published(p.uploaded_at)
        fe.description(", ".join(t.name for t in p.tags))
        fe.enclosure(
            url=f"{request.host_url[:-1]}{p.file_url}",
            # No fucking idea why we need encoding lol
            length=str(p.filesize).encode("utf-8"),
            # length=file.filesize.to_bytes(
            #     (file.filesize.bit_length() + 7) // 8, "big"
            # ),
            type=guess_type(p.file_url)[0],
        )

    return fg
