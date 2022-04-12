# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 03:10:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-12 16:35:16
import traceback

from flask import request, flash, redirect
from werkzeug.exceptions import HTTPException

from Onani.controllers.database.errors import log_error

from . import main
from .api import make_api_response


@main.app_errorhandler(Exception)
def error_handler(e):
    print(traceback.print_tb(e.__traceback__))  # DEBUG
    code = e.code if isinstance(e, HTTPException) else 500
    if request.path.startswith("/api/") or request.path.startswith("/admin/api/"):
        return make_api_response(error=str(e), code=code)

    if isinstance(e, HTTPException) and e.code == 401:
        flash("You must login to do this.")
        return redirect("/login/")

    if code == 500:
        # we log the error and get the error id
        error = log_error(e)
        return (
            f"""Error id: <strong>{error.id}</strong><br>
                HTTP error code: <strong>{code}</strong><br>
                Error: <span style="border: 2px solid black">{str(e)}</span>
                """,
            code,
        )
    return str(e), code
