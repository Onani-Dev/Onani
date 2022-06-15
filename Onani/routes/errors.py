# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-12 03:10:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-06-15 14:51:28
import traceback

from flask import current_app, flash, redirect, request, render_template, url_for, abort
from Onani.controllers.database.errors import log_error
from werkzeug.exceptions import HTTPException

from . import main


@main.app_errorhandler(Exception)
def error_handler(e):
    # Print traceback if app is in testing mode
    if current_app.testing:
        print(traceback.print_tb(e.__traceback__))

    # IF the exception is anything other than an HTTPException it will be a 500 code
    code = e.code if isinstance(e, HTTPException) else 500

    if code == 500:
        # we log the error and get the error id
        error = log_error(e)
        return (
            render_template("/errors/500.jinja2", exception=e, error=error, code=code),
            code,
        )

    if isinstance(e, HTTPException):
        return render_template("/errors/all.jinja2", exception=e), code

    return str(e), code


@main.route("/403")
def make_403():
    abort(403)


@main.route("/404")
def make_404():
    abort(404)


@main.route("/415")
def make_415():
    abort(415)
