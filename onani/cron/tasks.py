# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-08-07 15:02:10
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-07 15:05:11


from typing import List
from . import crontab, db


@crontab.job(minute="*/1")
def remove_expired_bans():
    from onani.models import Ban
    from onani.services import delete_ban

    # Only query bans that have an expiry date set; permanent bans are never expired
    expiring_bans: List[Ban] = Ban.query.filter(Ban.expires.isnot(None)).all()

    for ban in expiring_bans:
        if ban.has_expired:
            delete_ban(ban.user)


@crontab.job(minute="*/1")
def run_scheduled_imports():
    import datetime
    from onani.models.scheduled_import import ScheduledImport
    from onani.services import enqueue_import_job

    due = ScheduledImport.query.filter_by(enabled=True).all()
    for task in due:
        if not task.is_due():
            continue
        try:
            _, queued = enqueue_import_job(task.url, task.creator_id or 1, task.cookies)
            task.last_run_at = datetime.datetime.now(datetime.timezone.utc)
            task.last_run_status = "QUEUED" if queued else "DISPATCHED"
            task.last_error = None
            db.session.commit()
        except Exception as exc:
            task.last_run_at = datetime.datetime.now(datetime.timezone.utc)
            task.last_run_status = "FAILED"
            task.last_error = str(exc)
            db.session.commit()
