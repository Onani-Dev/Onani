# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-03 14:46:19
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-03 14:47:09

def startswith_min(s: str, /, start: str, min_len: int) -> bool:
    """
    checks if 'start' is 's' or any shortening of 's'
    that is (the shortening) at least of lenght min_len
    """
    if len(start) < min_len:
        return False
    return s.startswith(start)
