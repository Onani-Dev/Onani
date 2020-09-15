# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 14:10:42
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-14 19:31:26

from flask import flash, jsonify, redirect, render_template
from werkzeug.exceptions import HTTPException

from . import main, main_api


@main.errorhandler(401)
def error401(e):
    flash("You must login to do this.")
    return redirect("/login")


@main.errorhandler(404)
@main.errorhandler(405)
def error4xx(e):
    return str(e)


@main_api.app_errorhandler(Exception)
def error_handler(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code
