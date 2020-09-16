# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-03 18:17:16
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-14 02:50:29
import html
import logging
import regex
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


def custom_emoji(string: str):
    print(string)
    emoji_table = {
        # "\ud808\udc31": """<img src="/svg/don.svg" class='emoji'></img>""",
        "\ufdfd": """<img src="/svg/desuwa.svg" class='emoji'></img>""",
        ":desuwa:": """<img src="/svg/desuwa.svg" class='emoji'></img>""",
        ":don:": """<img src="/svg/don.svg" class='emoji'></img>""",
        ":katsu": """<img src="/svg/katsu.svg" class='emoji'></img>""",
    }
    for emoji in emoji_table:
        print(emoji)
        string.replace(emoji, emoji_table[emoji])
    return string
