# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-27 20:18:57
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-05-27 20:22:35

from Onani.models.post.rating import PostRating


def str_to_rating(s: str, /) -> PostRating:
    """Finds the appropriate PostRating from a string"""
    s = s.lower().strip()
    if s == "s":
        return PostRating.SAFE
    elif s == "q":
        return PostRating.QUESTIONABLE
    elif s == "e":
        return PostRating.EXPLICIT
    raise ValueError(f"No PostRating for string '{s}'")
