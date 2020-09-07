# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-31 18:25:05
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-07 12:40:25

import inspect
import logging
import time
from datetime import datetime

import pymongo


class EventLogger(logging.Handler):
    """
    Onani Logger for events.
    """

    def __init__(self, mongo_uri):
        logging.Handler.__init__(self)
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client["OnaniDB"]
        self.logs = self.db["OnaniLogs"]

    def emit(self, record):
        log_data = {
            "time": datetime.utcfromtimestamp(record.created),
            "name": record.name,
            "funcname": record.funcName,
            "level": record.levelname,
            "message": record.msg,
        }
        self.logs.insert_one(log_data)
