# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-16 21:12:40
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-03 18:33:29
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import humanize
from flask import flash, redirect, session, url_for
from flask_login import current_user, login_user

if TYPE_CHECKING:
    from Onani.models import User


def user_login(user: "User", password: str, otp: Optional[str] = None):
    # Check if password is correct
    if not user.check_password(password):
        # Password was wrong, show message
        flash("Invalid Login.", "error")
        return redirect(url_for("main.login"))

    if user.otp_enabled:
        if otp is None or not user.check_otp(otp):
            flash("Invalid OTP code.", "error")
            return redirect(url_for("main.login"))

    # Authentication passed
    return_url = session.pop("return_url", None)

    # Login to flask login
    login = login_user(user, duration=timedelta(days=7))

    if not login:
        # The login failed for some reason

        if user.ban:
            # The user is banned. They cannot login.
            flash(
                f"""
This account has been banned.
Reason: {user.ban.reason}
Expires: {f'{humanize.naturaltime(datetime.now(timezone.utc) - user.ban.expires)} (' + user.ban.expires.strftime('%d/%m/%Y %H:%M:%S') + ' UTC)' if user.ban.expires else 'Never'}
""",
                "error",
            )

            return redirect(url_for("main.login"))

        if user.is_deleted:
            # The user is deleted. They can never login again.
            flash("This user account has been deleted.", "error")
            return redirect(url_for("main.login"))

    # create the response object to add a cookie to
    response = redirect(return_url or url_for("main.get_user", user_id=current_user.id))

    # Set the currently logged in user's ID as a cookie for javascript to interact with
    response.set_cookie("current_user_id", str(current_user.id))

    # Return the redirect
    return response
