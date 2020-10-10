# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-03 18:17:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-11 02:35:51
import html
import logging
import random
import secrets
import string
from datetime import datetime
from typing import List, Tuple

import regex
from flask import Response
from json import dumps

from .controllers.logger import EventLogger


def setup_logger(
    name, mongo_uri="mongodb://localhost:27017/", level: int = logging.INFO
) -> logging.Logger:
    logdb = EventLogger(mongo_uri)
    logdb.setLevel(level)
    log = logging.getLogger(name)
    log.addHandler(logdb)
    log.setLevel(level)
    return log


def json_object_serialize(o):
    if isinstance(o, datetime):
        return o.timestamp()

    if "to_dict" in dir(o):
        return o.to_dict()


def html_escape(string: str) -> str:
    """```raw
    Escape HTML to prevent XSS attacks

    Args:
        string (str): The text to escape

    Returns:
        str: The escaped string
    """
    return html.escape(string)


def is_safe_username(username: str) -> bool:
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


def is_safe_email(email: str) -> bool:
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


def is_legal_password(password: str) -> bool:
    """```raw
    Check a password for legality

    Args:
        password (str): The password to check

    Returns:
        bool: if the password is legal or not
    """
    if len(password) < 4:
        return False
    for char in password:
        if char in string.whitespace:
            return False

    return True


def make_api_response(
    data: dict = dict(), error: str = None, code: int = 200
) -> Tuple[Response, int]:
    """```raw
    Make a response for the API

    Args:
        data (dict, optional): Python Dictionary to add to response. Defaults to dict().
        error (str, optional): The error (If any). Defaults to None.
        code (int, optional): The HTTP status code. Defaults to 200.

    Returns:
        Tuple[Response, int]: The Response and status code ready for flask
    """
    ok = True
    if code in range(400, 600):
        ok = False
    data["ok"] = ok
    data["error"] = error
    return (
        Response(
            dumps(data, default=json_object_serialize), mimetype="application/json"
        ),
        code,
    )


def parse_tag(tag: str) -> str:
    """```raw
    Parse a string to be a safe tag.

    Args:
        tag (str): The tag string to parse

    Returns:
        str: The safe tag
    """
    return html_escape(tag.strip().replace(" ", "_").lower())


def parse_tags(tags: List[str]) -> List[str]:
    """```raw
    The same as parse_tag, but for lists of strings.

    Args:
        tags (List[str]): The list of tag strings

    Returns:
        List[str]: The parsed list of tag strings
    """
    tgs = set()
    for tag in tags:
        tgs.add(parse_tag(tag))
    return list(tgs)


def random_username() -> str:
    return "User_" + "".join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(6)
    )


def create_api_key() -> str:
    return secrets.token_urlsafe(32)


def sanitize(query: str) -> str:
    return query.replace("function()", "")

