# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 03:10:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-12 03:13:26
import traceback

from flask import request, flash, redirect
from werkzeug.exceptions import HTTPException

from . import main
from .api import make_api_response


@main.app_errorhandler(Exception)
def error_handler(e):
    code = e.code if isinstance(e, HTTPException) else 500
    if request.path.startswith("/api/"):
        return make_api_response(error=str(e), code=code)

    if isinstance(e, HTTPException) and e.code == 401:
        flash("You must login to do this.")
        return redirect("/login")

    print(traceback.print_tb(e.__traceback__))  # DEBUG
    return str(e), code
