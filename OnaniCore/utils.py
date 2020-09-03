# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-03 18:17:16
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-03 21:52:24
import logging

from .controllers.logger import EventLogger


def setup_logger(name, mongo_uri="mongodb://localhost:27017/") -> logging.Logger:
    logdb = EventLogger("mongodb://localhost:27017/")
    logdb.setLevel(logging.INFO)
    log = logging.getLogger(name)
    log.addHandler(logdb)
    return log
