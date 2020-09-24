# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-09-12 14:10:42
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-24 15:05:51

from flask import flash, jsonify, redirect, render_template, request
from werkzeug.exceptions import HTTPException
from OnaniCore import *
from . import main


@main.app_errorhandler(Exception)
def error_handler(e):
    if request.path.startswith("/api/"):
        code = 500
        if isinstance(e, HTTPException) or isinstance(e, OnaniApiError):
            code = e.code
        return jsonify({"ok": False, "error": str(e)}), code

    if isinstance(e, HTTPException):
        if e.code == 401:
            flash("You must login to do this.")
            return redirect("/login")
    return str(e)

