# -*- coding: utf-8 -*-
import datetime

from . import db


class ImportJob(db.Model):
    """Persistent record of a manually-triggered import task."""

    __tablename__ = "import_jobs"

    id: int = db.Column(db.Integer, primary_key=True)

    # Celery task UUID
    task_id: str = db.Column(db.String(36), nullable=False, index=True)

    url: str = db.Column(db.String, nullable=False)

    user_id: int = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # PENDING / PROGRESS / SUCCESS / FAILURE / REVOKED / QUEUED
    # QUEUED means the job is waiting for another import from the same domain
    # to finish before it is dispatched to Celery.
    status: str = db.Column(db.String(20), nullable=False, default="PENDING")

    # Hostname extracted from ``url`` (e.g. "www.reddit.com").  Used to
    # serialise concurrent imports from the same extractor domain.
    domain: str = db.Column(db.String(253), nullable=True, index=True)

    # Stored parameters for QUEUED jobs that haven't been dispatched yet.
    # Currently holds: {"cookies_content": "<plaintext cookies>"}
    queue_meta: dict = db.Column(db.JSON, nullable=True)

    # Full Celery result dict once the task completes
    result: dict = db.Column(db.JSON, nullable=True)

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    finished_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True), nullable=True
    )

    user = db.relationship(
        "User",
        backref=db.backref("import_jobs", lazy="dynamic", passive_deletes=True),
    )

    def __repr__(self):
        return f"<ImportJob {self.id} task={self.task_id!r} status={self.status!r}>"
