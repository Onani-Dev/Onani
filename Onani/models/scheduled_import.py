# -*- coding: utf-8 -*-
import datetime

from . import db


class ScheduledImport(db.Model):
    """A recurring import task that fires at a fixed interval."""

    __tablename__ = "scheduled_imports"

    id: int = db.Column(db.Integer, primary_key=True)

    label: str = db.Column(db.String(200), nullable=True)

    url: str = db.Column(db.String, nullable=False)

    # How often to run, in minutes (minimum 30).
    interval_minutes: int = db.Column(db.Integer, nullable=False, default=1440)

    enabled: bool = db.Column(db.Boolean, nullable=False, default=True, server_default="true")

    # Cookies file contents (plain text netscape/header format), stored admin-side.
    cookies: str = db.Column(db.Text, nullable=True)

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    last_run_at: datetime.datetime = db.Column(db.DateTime(timezone=True), nullable=True)

    # 'DISPATCHED', 'QUEUED', 'FAILED', or None
    last_run_status: str = db.Column(db.String(20), nullable=True)

    last_error: str = db.Column(db.Text, nullable=True)

    creator_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def is_due(self) -> bool:
        """Return True if this task should run now."""
        if not self.enabled:
            return False
        if self.last_run_at is None:
            return True
        now = datetime.datetime.now(datetime.timezone.utc)
        last = self.last_run_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=datetime.timezone.utc)
        return (now - last).total_seconds() >= self.interval_minutes * 60

    def __repr__(self):
        return f"<ScheduledImport {self.id} {self.url!r}>"
