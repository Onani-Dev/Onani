# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:10:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-24 21:39:27

from flask import flash, redirect, render_template, request
from OnaniCore import *
from OnaniCore.utils import make_api_response
from werkzeug.exceptions import HTTPException

from . import main


@main.app_errorhandler(Exception)
def error_handler(e):
    if request.path.startswith("/api/"):
        code = 500
        if isinstance(e, HTTPException) or isinstance(e, OnaniApiError):
            code = e.code
        return make_api_response(error=str(e), code=code)

    if isinstance(e, HTTPException):
        if e.code == 401:
            flash("You must login to do this.")
            return redirect("/login")
    return str(e)

