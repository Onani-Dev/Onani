# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 02:27:38
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-30 04:41:23

from typing import Optional
from celery import shared_task

from . import db


@shared_task
def database_test(user_id: int) -> Optional[str]:
    from Onani.models import User

    user = User.query.filter_by(id=user_id).first()
    return str(user.username)
