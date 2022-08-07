# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-07 15:02:10
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-07 15:05:11


from typing import List
from . import crontab, db


@crontab.job(minute="*/1")
def remove_expired_bans():
    from Onani.models import Ban
    from Onani.controllers import delete_ban

    bans: List[Ban] = Ban.query.all()

    for ban in bans:
        if ban.has_expired:
            delete_ban(ban.user)
