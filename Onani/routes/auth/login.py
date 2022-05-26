# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:48:22
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-15 08:46:06
import html
from datetime import datetime, timedelta, timezone

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from Onani.controllers import user_login
from Onani.forms import LoginForm, RegistrationForm
from Onani.models import User

from . import db, main, limiter


@main.route("/login/", methods=["GET", "POST"])
@limiter.limit("10/minute", methods=["POST"])
def login():
    # We don't need to login again!
    if current_user.is_authenticated:
        return redirect(url_for("main.get_user", user_id=current_user.id))

    # Create the login form
    form = LoginForm(request.form)

    # The credentials have been posted
    if form.validate_on_submit():

        # Try to get the user
        user = User.query.filter_by(username=html.escape(form.username.data)).first()

        if not user:
            # user doesn't exist here
            flash("Invalid Login.", "error")
            return redirect(url_for("main.login"))

        return user_login(user, form.password.data)

    # Render the login page when visited.
    return render_template("/routes/login/index.jinja2", form=form)


@main.route("/register/", methods=["GET", "POST"])
@limiter.limit("1/hour", methods=["POST"])
def register():
    # The registration form object
    form = RegistrationForm()

    # Logged in users don't need to register again.
    if current_user.is_authenticated:
        return redirect(url_for("main.get_user", user_id=current_user.id))

    if form.validate_on_submit():
        user = User()
        try:
            user.username = form.username.data
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("main.register"))
        if form.email.data:
            try:
                user.email = form.email.data
            except ValueError as e:
                flash(str(e), "error")
                return redirect(url_for("main.register"))
        user.set_password(form.password.data)
        user.save_to_db()

        return user_login(user, form.password.data)

    # Render the registration page
    return render_template("/routes/register/index.jinja2", form=form)


@main.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("Successfully logged out.", "success")
    return redirect(url_for("main.login"))
