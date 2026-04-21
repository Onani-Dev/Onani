# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace


def _stub_inspect():
    class _Inspect:
        def active(self):
            return {}

        def reserved(self):
            return {}

        def scheduled(self):
            return {}

    return _Inspect()


def test_run_now_creates_import_job(admin_client, app, db, monkeypatch):
    client, admin = admin_client

    with app.app_context():
        from Onani.models import ScheduledImport, ImportJob
        from Onani.tasks import import_post

        task = ScheduledImport(
            label="Daily test",
            url="https://example.com/post/123",
            interval_minutes=1440,
            enabled=True,
            creator_id=admin.id,
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id

        monkeypatch.setattr(import_post.app.control, "inspect", lambda timeout=1.0: _stub_inspect())

        dispatched = {}

        def _fake_apply_async(*, args, task_id):
            dispatched["args"] = args
            dispatched["task_id"] = task_id
            return SimpleNamespace(id=task_id)

        monkeypatch.setattr(import_post, "apply_async", _fake_apply_async)

        response = client.post(
            "/api/v1/admin/scheduled-imports/run",
            data=json.dumps({"id": task_id}),
            content_type="application/json",
        )

        assert response.status_code == 200
        payload = json.loads(response.data)
        assert payload["queued"] is False
        assert payload["task_id"] == dispatched["task_id"]
        assert dispatched["args"] == ["https://example.com/post/123", admin.id, None]

        job = ImportJob.query.filter_by(task_id=payload["task_id"]).first()
        assert job is not None
        assert job.url == "https://example.com/post/123"
        assert job.user_id == admin.id
        assert job.status == "PENDING"

        task = ScheduledImport.query.get(task_id)
        assert task.last_run_status == "DISPATCHED"
        assert task.last_run_at is not None


def test_cron_queues_when_same_domain_job_exists(app, db, make_user, monkeypatch):
    with app.app_context():
        from Onani.cron.tasks import run_scheduled_imports
        from Onani.models import ImportJob, ScheduledImport
        from Onani.tasks import import_post

        user = make_user(username="scheduledadmin")

        existing_job = ImportJob(
            task_id="already-queued",
            url="https://example.com/post/existing",
            domain="example.com",
            user_id=user.id,
            status="QUEUED",
        )
        db.session.add(existing_job)

        scheduled_task = ScheduledImport(
            label="Queued test",
            url="https://example.com/post/new",
            interval_minutes=30,
            enabled=True,
            creator_id=user.id,
        )
        db.session.add(scheduled_task)
        db.session.commit()

        monkeypatch.setattr(import_post.app.control, "inspect", lambda timeout=1.0: _stub_inspect())

        dispatched = {"count": 0}

        def _fake_apply_async(*, args, task_id):
            dispatched["count"] += 1
            return SimpleNamespace(id=task_id)

        monkeypatch.setattr(import_post, "apply_async", _fake_apply_async)

        run_scheduled_imports()

        queued_job = (
            ImportJob.query
            .filter(ImportJob.task_id != "already-queued")
            .order_by(ImportJob.id.desc())
            .first()
        )
        assert queued_job is not None
        assert queued_job.url == "https://example.com/post/new"
        assert queued_job.domain == "example.com"
        assert queued_job.status == "QUEUED"
        assert queued_job.queue_meta is None
        assert dispatched["count"] == 0

        db.session.refresh(scheduled_task)
        assert scheduled_task.last_run_status == "QUEUED"
        assert scheduled_task.last_run_at is not None