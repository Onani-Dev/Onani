# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-18 21:17:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 13:58:56
from flask_wtf import FlaskForm
from Onani.models import UserSettings
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp
from wtforms.widgets import ColorInput


class AccountSettingsForm(FlaskForm):
    nickname = StringField(
        "Change Nickname",
        render_kw={"autocapitalize": "off", "autocomplete": "off"},
    )

    email = StringField(
        "Change Email",
        render_kw={"autocapitalize": "off", "autocomplete": "off"},
    )

    current_password = PasswordField(
        "Current Password",
        render_kw={
            "placeholder": "Current Password",
            "autocapitalize": "off",
            "autocomplete": "off",
        },
    )
    new_password = PasswordField(
        "New Password",
        render_kw={
            "placeholder": "New Password",
            "autocapitalize": "off",
            "autocomplete": "off",
        },
        validators=[
            EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm_new_password = PasswordField(
        "Confirm Password",
        render_kw={
            "placeholder": "Confirm New Password",
            "id": "profile-settings-password-confirm",
            "autocapitalize": "off",
        },
    )
    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "class": "profile-settings-submit",
            "data-submit-for": "settings-account",
            "type": "button",
            "id": "settings-account-submit",
        },
    )


class AccountProfileForm(FlaskForm):
    profile_picture = HiddenField(
        "Profile Picture",
        render_kw={
            "id": "hidden-base64-profile-picture",
        },
    )

    biography = TextAreaField(
        "Biography",
        render_kw={"id": "profile-settings-bio", "cols": "30", "rows": "10"},
    )

    profile_colour = StringField(
        "Profile Colour",
        render_kw={
            "id": "profile-colour",
        },
        widget=ColorInput(),
    )

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "class": "profile-settings-submit",
            "data-submit-for": "settings-profile",
            "type": "button",
            "id": "settings-profile-submit",
        },
    )
