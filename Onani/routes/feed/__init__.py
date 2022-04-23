# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-23 14:56:46
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-24 00:27:27

from datetime import datetime, timezone
from typing import Callable
from flask import Response, url_for
from feedgen.feed import FeedGenerator

from .. import rss, atom


def make_feed_generator() -> FeedGenerator:
    """Makes a FeedGenerator with some fields already filled"""
    fg = FeedGenerator()
    # fg.author({"name": "Onani", "email": "onani@onani.xyz"})
    fg.logo(url_for("static", filename="android-chrome-512x512.png", _external=True))
    fg.language("en")
    fg.lastBuildDate(datetime.now(timezone.utc))
    return fg


def feed(rule: str, *args, **kwargs) -> Callable:
    """
    Decorator to register a atom/RSS feed
    The decorated function must return a FeedGenerator
    """

    def feed_decorator(func: Callable) -> Callable:
        def atom_feed() -> str:
            """Returns a HTML response for an atom feed"""
            return Response(func().atom_str(pretty=False), mimetype="text/xml")

        def rss_feed() -> str:
            """Returns a HTML response for a RSS feed"""
            return Response(func().rss_str(pretty=False), mimetype="text/xml")

        atom.add_url_rule(rule, view_func=atom_feed, *args, **kwargs)
        rss.add_url_rule(rule, view_func=rss_feed, *args, **kwargs)
        return atom_feed

    return feed_decorator


# def feed(func: Callable, rule: str, *args, **kwargs) -> Callable:
#     """
#     Decorator to register a atom/RSS feed
#     The decorated function must return a FeedGenerator
#     """

#     def atom_feed() -> str:
#         """Returns a HTML response for an atom feed"""
#         return func().atom_str(pretty=True)

#     def rss_feed() -> str:
#         """Returns a HTML response for a RSS feed"""
#         return func().rss_str(pretty=True)

#     # atom.add_url_rule(rule, view_func=atom_feed, *args, **kwargs)
#     atom.route(atom_feed, rule, *args, **kwargs)
#     rss.route(rss_feed, rule, *args, **kwargs)
#     return atom_feed


from . import posts
