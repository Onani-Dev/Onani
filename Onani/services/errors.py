# -*- coding: utf-8 -*-
from Onani.models import Error
from traceback_with_variables import format_exc

from Onani import db


def log_error(e: Exception) -> Error:
    """Log an exception to the database and return the created Error record."""
    traceback = format_exc(e)
    err = Error(traceback=traceback, exception_type=str(type(e).__name__))
    db.session.add(err)
    db.session.commit()
    return err
