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

    # Only query bans that have an expiry date set; permanent bans are never expired
    expiring_bans: List[Ban] = Ban.query.filter(Ban.expires.isnot(None)).all()

    for ban in expiring_bans:
        if ban.has_expired:
            delete_ban(ban.user)
