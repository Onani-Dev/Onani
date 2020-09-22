# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-31 18:25:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-09 13:00:45

import inspect
import logging
import time
from datetime import datetime

import pymongo
from dateutil import tz


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
            "time": datetime.utcfromtimestamp(record.created).replace(
                tzinfo=tz.tzutc()
            ),
            "name": record.name,
            "funcname": record.funcName,
            "level": record.levelname,
            "message": record.msg,
        }
        self.logs.insert_one(log_data)
