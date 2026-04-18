# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-03 14:46:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 11:20:30

import re
from typing import List, Optional, Tuple, Union

from flask import request


def startswith_min(s: str, /, start: str, min_len: int) -> bool:
    """
    checks if 'start' is 's' or any shortening of 's'
    that is (the shortening) at least of length min_len
    """
    if len(start) < min_len:
        return False
    return s.startswith(start)


def natural_join(l: List[str], *, max_length: Optional[int] = None) -> str:
    """
    Joins list [a,b,c] as "a, b, and c"
    If the length of the list is bigger than max_length, then
    max_length items will be joined, then "and X more"
    """
    if not l:  # Handles empty lists first
        return ""

    # If there's only one element, we'd run into wrong indexes,
    # so we handle that case too
    if len(l) == 1:
        return l[0]

    if max_length is not None and len(l) > max_length:  # In case there's too many
        extra = f"{len(l) - max_length} more"
        l = l[:max_length]  # We remove the excess
        l.append(extra)  # and replace it with "X more"

    return f"{', '.join(l[:-1])} and {l[-1]}"


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert a hex value into an RGB one.

    Args:
        hex_code (str): The hex code to convert

    Returns:
        Tuple[int, int, int]: The RGB tuple.
    """
    return tuple(int(hex_code.strip("#")[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a hex code string

    Args:
        rgb (Tuple[int, int, int]): The RGB values in a tuple

    Returns:
        str: The hex code
    """
    return "#%02x%02x%02x" % rgb


def colour_contrast(colour: str) -> str:
    """Get the colour contrast from a specified colour.

    Args:
        colour (str): The colour to get the background for

    Returns:
        str: The background colour
    """
    rgb = hex_to_rgb(colour)

    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255

    d = 0 if luminance > 0.5 else 255

    return rgb_to_hex((d, d, d))


def complete_file_url(file_url: str) -> str:
    """Get the full url for a file.

    Args:
        file_url (str): The partial url

    Returns:
        str: The full url
    """
    return f"{request.base_url}{file_url.lstrip('/')}"



_URL_RE = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}"
    r"|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}"
    r"|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}"
    r"|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)


def is_url(string: str) -> bool:
    """Check if a string is a url

    Args:
        string (str): The string to check

    Returns:
        bool: True if a url false if not
    """
    return bool(_URL_RE.match(string))


def url_hostname(url: str) -> Union[str, None]:
    """Returns the hostname of a url, or none

    Args:
        url (str): the url to return the hostname of

    Returns:
        Union[str, None]: The hostname or none
    """
    return url.split("/")[2] if is_url(url) else url or None

