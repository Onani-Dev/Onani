# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-11 20:11:48
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-11 21:15:12

import datetime
import enum
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import ChoiceType

from . import db

class Error(db.Model):
    """
    Error Models
    """

    __tablename__ = "errors"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    
    traceback = db.Column(db.String, nullable=False)


    def __repr__(self):
        return "<Error {0!r}>".format(self.__dict__)
