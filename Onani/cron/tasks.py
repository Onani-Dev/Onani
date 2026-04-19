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
    from Onani.services import delete_ban

    # Only query bans that have an expiry date set; permanent bans are never expired
    expiring_bans: List[Ban] = Ban.query.filter(Ban.expires.isnot(None)).all()

    for ban in expiring_bans:
        if ban.has_expired:
            delete_ban(ban.user)


@crontab.job(minute="*/1")
def run_scheduled_imports():
    import datetime
    from Onani.models.scheduled_import import ScheduledImport
    from Onani.tasks.importer import import_post

    due = ScheduledImport.query.filter_by(enabled=True).all()
    for task in due:
        if not task.is_due():
            continue
        task.last_run_at = datetime.datetime.now(datetime.timezone.utc)
        task.last_run_status = "DISPATCHED"
        task.last_error = None
        try:
            db.session.commit()
            import_post.delay(task.url, task.creator_id or 1, task.cookies)
        except Exception as exc:
            task.last_run_status = "FAILED"
            task.last_error = str(exc)
            db.session.commit()
