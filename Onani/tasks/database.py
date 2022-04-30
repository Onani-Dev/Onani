# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 02:27:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-30 16:38:52

from typing import Optional
from celery import shared_task

from . import db


@shared_task
def database_test(user_id: int) -> Optional[str]:
    from Onani.models import User, UserSchema

    return UserSchema().dump(User.query.filter_by(id=user_id).first())
