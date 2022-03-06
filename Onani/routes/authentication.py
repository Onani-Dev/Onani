# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-03 22:36:19
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 01:34:55
from datetime import datetime, timedelta

import humanize
from dateutil import tz
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from Onani.forms import LoginForm, RegistrationForm

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


@main.route("/register", methods=["GET", "POST"])
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
            except AssertionError as e:
                flash("Invalid Email.")
                return redirect(url_for("main.register"))
        user.set_password(form.password.data)
        user.save_to_db()

        # Account created.
        flash("Account created, You can now login.")
        return redirect(url_for("main.login"))

    # if not username and not password and not confirm:
    #     flash("🤨")
    #     return redirect("/register")
    # # Check password
    # if not password:
    #     flash("No password was entered.")
    #     return redirect("/register")

    #     # Check if passwords match
    # if password != confirm:
    #     flash("Passwords did not match.")
    #     return redirect("/register")

    # # Try to insert it into database
    # try:
    #     user = User(username=username, email="test@pee.com")
    #     user.set_password(password)
    #     user.save_to_db()
    # except Exception as e:
    #     # We couldn't.
    #     flash(str(e))
    #     return redirect("/register")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")
