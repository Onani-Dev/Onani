# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 13:31:11
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-13 20:34:34

from datetime import datetime, timedelta

import humanize
from dateutil import tz
from flask import (
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from OnaniCore import *

from .. import login_manager
from . import main, onaniDB


@login_manager.user_loader
def user_loader(username):
    try:
        user = onaniDB.get_user(username=username)
    except OnaniDatabaseException:
        return
    return user if not user.is_banned else None


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")
    if request.method == "GET":
        return render_template("/login.jinja2")
    else:
        if request.form["username"] == "" and request.form["password"] == "":
            flash("Enter something!")
            return redirect("/login")
        if request.form["username"] == "":
            flash("No username was given.")
            return redirect("/login")
        if request.form["password"] == "":
            flash("No password was given.")
            return redirect("/login")
        try:
            user = onaniDB.get_user(username=request.form["username"])
        except OnaniDatabaseException:
            flash("Account does not exist.")
            return redirect("/login")
        if user.authenticate(request.form["password"]):
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                if current_user.is_banned:
                    user_ban = current_user.get_ban()
                    if user_ban.has_expired:
                        current_user.unban()
                        return redirect(f"/users/{current_user.id}")
                    logout_user()
                    flash(
                        f"This account has been banned.\nReason: {user_ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user_ban.expires.astimezone(tz.tzlocal()))} ({user_ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect("/login")
                return redirect(f"/users/{current_user.id}")
            flash("This account has been deleted.")
            return redirect("/login")
        flash("Invalid Password.")
        return redirect("/login")


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")
    if request.method == "GET":
        return render_template("/register.jinja2")
    else:
        if " " in request.form["username"]:
            flash("Usernames cannot have whitespace.")
            return redirect("/register")
        if not request.form["password"] == request.form["confirm-password"]:
            flash("Passwords did not match.")
            return redirect("/register")
        try:
            user = onaniDB.add_user(
                username=html_escape(request.form["username"]),
                email=html_escape(request.form["email"])
                if request.form.get("email") != ""
                else None,
                password=request.form["password"],
            )
        except OnaniDatabaseException as e:
            flash(e.msg)
            return redirect("/register")
        flash("Account created, You can now login.")
        return redirect("/login")


@main.route("/logout")
@login_required
def logout():
    current_user.deauthenticate()
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
