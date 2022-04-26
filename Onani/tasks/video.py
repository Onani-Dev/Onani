# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-26 00:35:31
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-26 01:39:54


from . import dramatiq


@dramatiq.actor()
def test(string):
    print(string)
