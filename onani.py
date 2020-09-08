# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-09 03:41:17

import logging
import os
import random
from datetime import datetime, timedelta

import humanize
import pymongo
from dateutil import tz
from flask import (
    Flask,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sockets import Sockets

from OnaniCore import *

app = Flask(
    __name__,
    static_url_path="",
    static_folder="OnaniFrontend/static",
    template_folder="OnaniFrontend/views",
)
# Temporary secret key; Change to config generated one
app.config["SECRET_KEY"] = b"\xd2\xc0\xe1\x00$\x06\x19\xef"

onaniDB = DatabaseController("mongodb://localhost:27017/")
login_manager = LoginManager()
login_manager.init_app(app)
sockets = Sockets(app)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@login_manager.user_loader
def user_loader(username):
    try:
        user = onaniDB.get_user(username=username)
    except ValueError:
        return
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("/login.html.jinja2", current_user=current_user)
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
        except ValueError:
            flash("Account does not exist.")
            return redirect("/login")
        if user.authenticate(request.form["password"]):
            login = login_user(user, duration=timedelta(days=60), remember=True)
            if login:
                if current_user.is_banned:
                    user_ban = current_user.get_ban()
                    if user_ban.has_expired:
                        current_user.unban()
                        return redirect("/")
                    logout_user()
                    print(user_ban.expires)
                    flash(
                        f"This account has been banned.\nReason: {user_ban.reason}\nExpires: {humanize.naturaltime(datetime.utcnow().replace(tzinfo=tz.tzutc()) - user_ban.expires.astimezone(tz.tzlocal()))} ({user_ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
                    )
                    return redirect("/login")
                return redirect("/")
            flash("This account has been deleted.")
            return redirect("/login")
        flash("Invalid Password.")
        return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    current_user.deauthenticate()
    logout_user()
    flash("Successfully logged out.")
    return redirect("/login")


@app.route("/")
@app.route("/posts")
def index():
    return render_template(
        "/index.html.jinja2",
        current_user=current_user,
        tags=onaniDB.get_tags(limit=25, sort="post_count"),
    )


@app.route("/profile")
@login_required
def profile():
    return current_user.username


@app.errorhandler(401)
def error401(e):
    flash("You must login to do this.")
    return redirect("/login")


if __name__ == "__main__":
    app.run()
