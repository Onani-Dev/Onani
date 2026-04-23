# -*- coding: utf-8 -*-
import datetime
import uuid
from urllib.parse import urlparse

from onani import db
from onani.models import ImportJob
from onani.tasks import import_post


def _collect_live_import_task_ids() -> set[str]:
    inspect = import_post.app.control.inspect(timeout=1.0)
    active_data = inspect.active() or {}
    reserved_data = inspect.reserved() or {}
    scheduled_data = inspect.scheduled() or {}

    live_task_ids = set()
    for payload in (active_data, reserved_data):
        for tasks in payload.values():
            for task in tasks or []:
                task_id = task.get("id")
                if task_id:
                    live_task_ids.add(task_id)

    for tasks in scheduled_data.values():
        for task in tasks or []:
            request = task.get("request") if isinstance(task, dict) else None
            task_id = request.get("id") if isinstance(request, dict) else None
            if task_id:
                live_task_ids.add(task_id)

    return live_task_ids


def _reconcile_stale_pending_jobs(domain: str, cutoff: datetime.datetime) -> None:
    if not domain:
        return

    try:
        live_task_ids = _collect_live_import_task_ids()
        stale_jobs = (
            ImportJob.query
            .filter(
                ImportJob.domain == domain,
                ImportJob.status == "PENDING",
                ImportJob.created_at > cutoff,
            )
            .all()
        )

        for stale_job in stale_jobs:
            if stale_job.task_id in live_task_ids:
                continue

            task_state = import_post.AsyncResult(stale_job.task_id).state
            if task_state in ("SUCCESS", "FAILURE", "REVOKED"):
                stale_job.status = task_state
            elif task_state == "PENDING":
                stale_job.status = "REVOKED"
                stale_job.result = {
                    "error": "Task was orphaned after worker restart and has been revoked."
                }
            else:
                continue

            stale_job.finished_at = datetime.datetime.now(datetime.timezone.utc)

        db.session.commit()
    except Exception:
        db.session.rollback()


def enqueue_import_job(url: str, user_id: int, cookies_content: str = None) -> tuple[str, bool]:
    """Create an ImportJob and dispatch or queue it using the standard importer flow."""
    domain = urlparse(url).hostname or ""
    task_id = str(uuid.uuid4())
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12)

    _reconcile_stale_pending_jobs(domain, cutoff)

    active = (
        ImportJob.query
        .filter(
            ImportJob.domain == domain,
            ImportJob.status.in_(["PENDING", "QUEUED"]),
            ImportJob.created_at > cutoff,
        )
        .first()
    ) if domain else None

    if active:
        job = ImportJob(
            task_id=task_id,
            url=url,
            domain=domain or None,
            user_id=user_id,
            status="QUEUED",
            queue_meta={"cookies_content": cookies_content} if cookies_content else None,
        )
        db.session.add(job)
        db.session.commit()
        return task_id, True

    job = ImportJob(
        task_id=task_id,
        url=url,
        domain=domain or None,
        user_id=user_id,
        status="PENDING",
    )
    db.session.add(job)
    db.session.commit()

    try:
        import_post.apply_async(
            args=[url, user_id, cookies_content],
            task_id=task_id,
        )
    except Exception as exc:
        job.status = "FAILURE"
        job.result = {"error": f"Failed to dispatch import task: {exc}"}
        job.finished_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        raise

    return task_id, False