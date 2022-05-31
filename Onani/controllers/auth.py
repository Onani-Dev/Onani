# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-16 21:12:40
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-31 13:38:42
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import humanize
from flask import flash, redirect, session, url_for
from flask_login import current_user, login_user

if TYPE_CHECKING:
    from Onani.models import User


def user_login(user: "User", password: str):
    # Check if password is correct
    if user.check_password(password):
        # Authentication passed

        return_url = session.get("return_url")
        session.clear()

        # Login to flask login
        login = login_user(user, duration=timedelta(days=7))

        if not login:
            # The login failed for some reason

            if user.ban:
                # The user is banned. They cannot login.
                flash(
                    f"This account has been banned.\nReason: {user.ban.reason}\nExpires: {humanize.naturaltime(datetime.now(timezone.utc) - user.ban.expires)} ({user.ban.expires.strftime('%d/%m/%Y %H:%M:%S')} UTC)",
                    "error",
                )

                return redirect(url_for("main.login"))

            if user.is_deleted:
                # The user is deleted. They can never login again.
                flash("This user account has been deleted.", "error")
                return redirect(url_for("main.login"))

        return redirect(return_url or url_for("main.get_user", user_id=current_user.id))

    # Password was wrong, show message
    flash("Invalid Login.", "error")
    return redirect(url_for("main.login"))
