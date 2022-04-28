# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-26 00:35:31
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-28 21:07:18


from . import dramatiq


@dramatiq.actor(store_results=True)
def test(string):
    print(string)
    return string
