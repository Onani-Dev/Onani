# -*- coding: utf-8 -*-
import datetime

from . import db


class PostView(db.Model):
    """Tracks individual view events for posts, used for the hot-posts algorithm."""

    __tablename__ = "post_views"
    __table_args__ = (
        db.Index("ix_post_views_post_viewed", "post_id", "viewed_at"),
    )

    id: int = db.Column(db.Integer, primary_key=True)

    post_id: int = db.Column(
        db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )

    viewed_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
    )
