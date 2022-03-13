# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:48:22
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 22:44:10
from datetime import datetime, timedelta

import humanize
from dateutil import tz
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from Onani.forms import LoginForm, RegistrationForm
from Onani.models import User

from . import db, main


@main.route("/login/", methods=["GET", "POST"])
def login():
    # Create the login form
    form = LoginForm(request.form)

    # We don't need to login again!
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")

    # Render the login page when visited.
    if request.method == "GET":
        return render_template("/login.jinja2", form=form)

    # The credentials have been posted
    if request.method == "POST" and form.validate():
        # Try to get the user
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            # user doesn't exist here
            flash("Account does not exist.")
            return redirect(url_for("main.login"))

        # Check if password is correct
        if user.check_password(form.password.data):
            # Authentication passed

            # Login to flask login
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                # User is active
                if current_user.is_banned:
                    # They banned doe :flushed:

                    if user.ban.has_expired:
                        # their ban has expired, continue login
                        current_user.ban = None
                        db.session.commit()
                        return redirect(f"/users/{current_user.id}")

                    # They are still banned, logout and show message
                    logout_user()
                    flash(
                        f"This account has been banned.\nReason: {user.ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user.ban.expires.astimezone(tz.tzlocal()))} ({user.ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect(url_for("main.login"))

                return redirect(f"/users/{current_user.id}")

        # Password was wrong, show message
        flash("Invalid Login.")
        return redirect(url_for("main.login"))


@main.route("/register/", methods=["GET", "POST"])
def register():
    # The registration form object
    form = RegistrationForm(request.form)

    # Logged in users don't need to register again.
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")

    # Render the registration page
    if request.method == "GET":
        return render_template("/register.jinja2", form=form)

    #
    if request.method == "POST" and form.validate():
        user = User(username=form.username.data)
        if form.email.data:
            try:
                user.email = form.email.data
            except ValueError as e:
                flash("Invalid Email.")
                return redirect(url_for("main.register"))
        user.set_password(form.password.data)
        user.save_to_db()

        # Account created.
        flash("Account created, You can now login.")
        return redirect(url_for("main.login"))


@main.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
