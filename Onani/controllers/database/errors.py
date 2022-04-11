# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-11 21:20:25
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-11 22:26:19

import uuid
from . import db
from traceback_with_variables import format_exc
from Onani.models.error import Error

def log_error(e: Exception) -> uuid.UUID:
    """Logs an exception to the DB

    Args:
        e (Exception): the exception to log

    Returns:
        UUID: the identifier for the error
    """
    traceback = format_exc(e)

    err = Error(traceback = traceback)

    db.session.add(err)
    db.session.commit()
    return err.id