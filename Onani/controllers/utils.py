# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-03 14:46:19
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-18 20:06:00

from typing import List, Optional


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
    if not l: # Handles empty lists first
        return ""

    # If there's only one element, we'd run into wrong indexes, 
    # so we handle that case too
    if len(l) == 1:
        return l[0]

    if len(l) > max_lenght: # In case there's too many
        extra = f"{len(l) - max_lenght} more"
        l = l[:max_lenght] # We remove the excess
        l.append(extra) # and replace it with "X more"

    return f"{', '.join(l[:-1])}, and {l[-1]}"   
