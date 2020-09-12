# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 14:10:42
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-12 14:25:18
from flask import flash, redirect, render_template

from . import main


@main.errorhandler(401)
def error401(e):
    flash("You must login to do this.")
    return redirect("/login")
