# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-03 14:46:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-16 07:57:16

from typing import List, Optional, Tuple

from flask import flash, request


def startswith_min(s: str, /, start: str, min_len: int) -> bool:
    """
    checks if 'start' is 's' or any shortening of 's'
    that is (the shortening) at least of lenght min_len
    """
    if len(start) < min_len:
        return False
    return s.startswith(start)


def natural_join(l: List[str], *, max_lenght: Optional[int] = None) -> str:
    """
    Joins list [a,b,c] as "a, b, and c"
    If the lenght of the list is bigger than max_lenght, then
    max_lenght items will be joined, then "and X more"
    """
    if not l:  # Handles empty lists first
        return ""

    # If there's only one element, we'd run into wrong indexes,
    # so we handle that case too
    if len(l) == 1:
        return l[0]

    if len(l) > max_lenght:  # In case there's too many
        extra = f"{len(l) - max_lenght} more"
        l = l[:max_lenght]  # We remove the excess
        l.append(extra)  # and replace it with "X more"

    return f"{', '.join(l[:-1])}, and {l[-1]}"


def get_page() -> int:
    """Get the current page from the current request's params.

    Returns:
        int: The current page
    """
    # Get the page, will default to 0 if there is no args
    page = request.args.get("p", "0")

    # Convert the page to an int if it is a digit, if it is not, default to 0
    page = int(page) if page.isdigit() else 0

    return page


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


def flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, "error")  # f"Error in the {field.capitalize()} field: {error}"
