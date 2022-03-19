# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:48:22
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-19 16:16:33
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
    # We don't need to login again!
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")

    # Create the login form
    form = LoginForm(request.form)

    # The credentials have been posted
    if request.method == "POST" and form.validate():

        # Try to get the user
        user = User.query.filter_by(username=form.username.data).first()

        if not user:
            # user doesn't exist here
            flash("Account does not exist.")
            return redirect(url_for("main.login"))

        # Check if password is correct
        if user.check_password(form.password.data):
            # Authentication passed

            # Login to flask login
            login = login_user(user, duration=timedelta(days=7))

            if not login:
                # The login failed for some reason

                if user.ban:
                    # The user is banned. They cannot login.
                    flash(
                        f"This account has been banned.\nReason: {user.ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user.ban.expires.astimezone(tz.tzlocal()))} ({user.ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect(url_for("main.login"))

                if user.is_deleted:
                    # The user is deleted. They can never login again.
                    flash("User is deleted.")
                    return redirect(url_for("main.login"))

            return redirect(f"/users/{current_user.id}")

        # Password was wrong, show message
        flash("Invalid Login.")
        return redirect(url_for("main.login"))

    # Render the login page when visited.
    return render_template("/login.jinja2", form=form)


@main.route("/register/", methods=["GET", "POST"])
def register():
    # The registration form object
    form = RegistrationForm(request.form)

    # Logged in users don't need to register again.
    if current_user.is_authenticated:
        return redirect(f"/users/{current_user.id}")

    if request.method == "POST" and form.validate():
        user = User()
        try:
            user.username = form.username.data
        except ValueError as e:
            flash(str(e))
            return redirect(url_for("main.register"))
        if form.email.data:
            try:
                user.email = form.email.data
            except ValueError as e:
                flash(str(e))
                return redirect(url_for("main.register"))
        user.set_password(form.password.data)
        user.save_to_db()

        # Account created.
        flash("Account created, You can now login.")
        return redirect(url_for("main.login"))

    # Render the registration page
    return render_template("/register.jinja2", form=form)


@main.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
