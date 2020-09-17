# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-03 18:17:16
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 22:18:32
import html
import logging
import string

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


def check_is_safe_username(username: str) -> bool:
    """```raw
    Check if username is legal

    Args:
        username (str): Username to check

    Returns:
        bool: True if safe False if not
    """
    banned_chars = "!\"#$%&'()*+,/:;<=>?@[\\]^`{|}~ \t\n\r\x0b\x0c"
    for char in username:
        if char in banned_chars:
            return False
    return True


def check_if_safe_email(email: str) -> bool:
    """```raw
    Check if email is safe

    Args:
        email (str): Email to check

    Returns:
        bool: True if safe False if not
    """
    re = r"""(?:[a-z0-9!#$%&'+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
    if regex.match(re, email):
        return True
    return False


def check_if_legal_password(password: str):
    if len(password) < 4:
        return False
    for char in password:
        if char in string.whitespace:
            return False

    return True
