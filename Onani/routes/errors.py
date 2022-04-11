# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 03:10:42
# @Last Modified by:   Mattlau04
# @Last Modified time: 2022-04-11 22:32:14
import traceback

from flask import request, flash, redirect
from werkzeug.exceptions import HTTPException

from Onani.controllers.database.errors import log_error

from . import main
from .api import make_api_response


@main.app_errorhandler(Exception)
def error_handler(e):
    code = e.code if isinstance(e, HTTPException) else 500
    if request.path.startswith("/api/"):
        return make_api_response(error=str(e), code=code)

    if isinstance(e, HTTPException) and e.code == 401:
        flash("You must login to do this.")
        return redirect("/login/")

    print(traceback.print_tb(e.__traceback__))  # DEBUG
    # we log the error and get the error id
    error_id = log_error(e)
    return f"""Error id: <strong>{error_id}</strong><br>
HTTP error code: <strong>{code}</strong><br>
Error: <span style="border: 2px solid black">{str(e)}</span>"""
