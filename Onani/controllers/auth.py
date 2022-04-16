# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-16 21:12:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-16 21:17:19
from datetime import datetime, timedelta, timezone

import humanize
from flask import flash, redirect, url_for
from flask_login import current_user, login_user
from Onani.models import User


def user_login(user: User, password: str):
    # Check if password is correct
    if user.check_password(password):
        # Authentication passed

        # Login to flask login
        login = login_user(user, duration=timedelta(days=7))

        if not login:
            # The login failed for some reason

            if user.ban:
                # The user is banned. They cannot login.
                flash(
                    f"This account has been banned.\nReason: {user.ban.reason}\nExpires: {humanize.naturaltime(datetime.now(timezone.utc) - user.ban.expires)} ({user.ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)"
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
