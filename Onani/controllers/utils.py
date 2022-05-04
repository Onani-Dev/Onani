# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-03 14:46:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:54:07

from typing import List, Optional

from flask import request


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
