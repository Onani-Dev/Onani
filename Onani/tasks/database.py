# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 02:27:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:42:58

from celery import shared_task

from . import db


@shared_task
def database_test(user):
    return str(user.id)
