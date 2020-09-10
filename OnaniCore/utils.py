# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-03 18:17:16
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-10 14:15:16
import html
import logging

from .controllers.logger import EventLogger


def setup_logger(
    name, mongo_uri="mongodb://localhost:27017/", level: int = logging.INFO
) -> logging.Logger:
    logdb = EventLogger("mongodb://localhost:27017/")
    logdb.setLevel(level)
    log = logging.getLogger(name)
    log.addHandler(logdb)
    log.setLevel(level)
    return log


def html_escape(string: str):
    """```raw
    Escape HTML to prevent XSS attacks

    Args:
        string (str): The text to escape

    Returns:
        str: The escaped string
    """
    return html.escape(string)
