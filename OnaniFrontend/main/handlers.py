# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 14:10:42
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 21:23:46

from flask import flash, jsonify, redirect, render_template, request
from werkzeug.exceptions import HTTPException
from OnaniCore import *
from . import main, main_api


@main.app_errorhandler(401)
def error401(e):
    flash("You must login to do this.")
    return redirect("/login")


@main.app_errorhandler(Exception)
def html_error_handler(e):
    if request.path.startswith("/api/"):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        if isinstance(e, OnaniApiError):
            code = 400
        return jsonify({"ok": False, "error": str(e)}), code
    return str(e)

