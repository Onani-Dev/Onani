# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-09-12 13:31:11
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 21:27:42

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
from OnaniCore.utils import is_safe_email, is_safe_username
from .. import login_manager
from . import main, onaniDB


@login_manager.user_loader
def user_loader(user_id):
    try:
        user = onaniDB.get_user(id=user_id)
    except OnaniDatabaseException:
        return
    return user if not user.is_banned else None


@login_manager.request_loader
def request_loader(request):
    api_key = request.headers.get("Authorization")
    if api_key:
        user = onaniDB.get_user(api_key=api_key)
        if user is None:
            return
        return user if not user.is_banned else None
    return


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")
    if request.method == "GET":
        return render_template("/login.jinja2")
    else:
        if request.form["username"] == "" and request.form["password"] == "":
            # User entered nothing
            flash("Enter something!")
            return redirect("/login")

        if request.form["username"] == "":
            # User gave no username
            flash("No username was given.")
            return redirect("/login")

        if request.form["password"] == "":
            # User gave no password
            flash("No password was given.")
            return redirect("/login")

        # Try to get the user
        try:
            user = onaniDB.get_user(username=request.form["username"])
        except OnaniDatabaseException:
            # user doesn't exist here
            flash("Account does not exist.")
            return redirect("/login")

        # Check if password is correct
        if user.authenticate(request.form["password"]):
            # Authentication passed

            # Login to flask login
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                # User is active
                if current_user.is_banned:
                    # They banned doe :flushed:

                    # get ban from the ban database
                    user_ban = current_user.get_ban()

                    if user_ban.has_expired:
                        # their ban has expired, continue login
                        current_user.unban()
                        return redirect(f"/users/{current_user.id}")

                    # They are still banned, logout and show message
                    logout_user()
                    flash(
                        f"This account has been banned.\nReason: {user_ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user_ban.expires.astimezone(tz.tzlocal()))} ({user_ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect("/login")

                return redirect(f"/users/{current_user.id}")

            # Account is deleted, Show message
            flash("This account has been deleted.")
            return redirect("/login")

        # Password was wrong, show message
        flash("Invalid Password.")
        return redirect("/login")


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")
    if request.method == "GET":
        return render_template("/register.jinja2")
    else:
        if (
            request.form["username"] == ""
            and request.form["password"] == ""
            and request.form["confirm-password"] == ""
        ):
            flash("🤨")
            return redirect("/register")

        # Check username for illegal chars
        if not is_safe_username(request.form["username"]):
            flash("Username has illegal characters.")
            return redirect("/register")

        # Check if email is valid
        if request.form["email"] != "":
            if not is_safe_email(request.form["email"]):
                flash("Email was invalid.")
                return redirect("/register")

        # Check password
        if request.form["password"] == "":
            flash("No password was entered.")
            return redirect("/register")

        # check password length
        if len(request.form["password"]) < 4:
            flash("Password is too short.")
            return redirect("/register")

        # Check if passwords match
        if not request.form["password"] == request.form["confirm-password"]:
            flash("Passwords did not match.")
            return redirect("/register")

        # Try to insert it into database
        try:
            user = onaniDB.add_user(
                username=html_escape(request.form["username"]),
                email=html_escape(request.form["email"])
                if request.form.get("email") != ""
                else None,
                password=request.form["password"],
            )
        except OnaniDatabaseException as e:
            # We couldn't.
            flash(e.msg)
            return redirect("/register")

        # Account created.
        flash("Account created, You can now login.")
        return redirect("/login")


@main.route("/logout")
@login_required
def logout():
    current_user.deauthenticate()
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
