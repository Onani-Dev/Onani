# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-31 18:25:05
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-31 21:45:08

import inspect
from datetime import datetime
import logging

from ..models.user import User


class EventLogger(logging.Handler):
    """
    Onani Logger for events.
    """

    def __init__(self, db):
        super().__init__(self)
        self.db = db

    def emit(self, record):
        tm = datetime.strftime("%Y-%m-%d %H:%M:%S", record.created)
        # TODO #26 WIP logger for onani database
