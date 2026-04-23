# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-11 21:20:25
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-05 02:38:19

from onani.models import Error
from traceback_with_variables import format_exc

from . import db


def log_error(e: Exception) -> Error:
    """Logs an exception to the DB

    Args:
        e (Exception): The exception to log

    Returns:
        Error: The logged error object
    """
    traceback = format_exc(e)

    err = Error(traceback=traceback, exception_type=str(type(e).__name__))

    db.session.add(err)
    db.session.commit()
    return err
