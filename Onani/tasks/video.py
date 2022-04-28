# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-26 00:35:31
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:18:58

from celery import shared_task


@shared_task
def test(string):
    return "".join(reversed(string))
