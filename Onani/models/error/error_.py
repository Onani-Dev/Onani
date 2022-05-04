# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-11 20:11:48
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:12:22

import datetime
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID

from . import db


class Error(db.Model):
    """
    Error Models
    """

    __tablename__ = "errors"

    id: UUID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    created_at: datetime.datetime = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    exception_type: str = db.Column(db.String, nullable=False)

    traceback: str = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Error '{self.id}'>"
