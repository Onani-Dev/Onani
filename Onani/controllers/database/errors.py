# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-04-11 21:20:25
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-12 16:29:38

import uuid

from Onani.models import Error
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

    err = Error(traceback=traceback)

    db.session.add(err)
    db.session.commit()
    return err
