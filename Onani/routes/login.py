# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 22:36:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-04 04:42:24
from datetime import datetime, timedelta

import humanize
from dateutil import tz
from flask import flash, jsonify, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from .. import login_manager
from ..models import Ban, Post, Tag, User, UserPermissions
from . import db, main


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return
    return user if not user.is_banned else None


@login_manager.request_loader
def request_loader(request):
    # Normal Login
    if request.authorization:
        username, password = (
            request.authorization.username,
            request.authorization.password,
        )

        user = User.query.filter_by(username=username).first()

        if user.check_password(password):
            return user if not user.is_banned else None

    if api_key := request.headers.get("Authorization"):
        user = User.query.filter_by(api_key=api_key).first()
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
        user = User.query.filter_by(username=request.form["username"]).first()
        if user is None:
            # user doesn't exist here
            flash("Account does not exist.")
            return redirect("/login")

        # Check if password is correct
        if user.check_password(request.form["password"]):
            # Authentication passed

            # Login to flask login
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                # User is active
                if current_user.is_banned:
                    # They banned doe :flushed:

                    if user.ban.has_expired:
                        # their ban has expired, continue login
                        current_user.unban()
                        return redirect(f"/users/{current_user.id}")

                    # They are still banned, logout and show message
                    logout_user()
                    flash(
                        f"This account has been banned.\nReason: {user.ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user.ban.expires.astimezone(tz.tzlocal()))} ({user.ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect("/login")

                return redirect(f"/users/{current_user.id}")

            # Account is deleted, Show message
            flash("This account has been deleted.")
            return redirect("/login")

        # Password was wrong, show message
        flash("Invalid Login.")
        return redirect("/login")


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")
    if request.method == "GET":
        return render_template("/register.jinja2")
    username = request.form["username"]
    password = request.form["password"]
    confirm = request.form["confirm-password"]
    if not username and not password and not confirm:
        flash("🤨")
        return redirect("/register")
    # Check password
    if not password:
        flash("No password was entered.")
        return redirect("/register")

        # Check if passwords match
    if password != confirm:
        flash("Passwords did not match.")
        return redirect("/register")

    # Try to insert it into database
    try:
        user = User(username=username, email="test@pee.com")
        user.set_password(password)
        user.save_to_db()
    except Exception as e:
        # We couldn't.
        flash(str(e))
        return redirect("/register")

    # Account created.
    flash("Account created, You can now login.")
    return redirect("/login")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
