# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-18 21:17:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 02:52:55
from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class AccountSettingsForm(FlaskForm):
    username = StringField(
        "Change Username",
        render_kw={
            "id": "profile-settings-name",
            "autocapitalize": "off",
        },
        validators=[Optional(), Length(min=4, max=32)],
    )

    email = StringField(
        "Change Email",
        render_kw={
            "id": "profile-settings-email",
            "autocapitalize": "off",
        },
        validators=[Optional(), Email()],
    )

    current_password = PasswordField(
        "Current Password",
        render_kw={
            "placeholder": "Current Password",
            "id": "profile-settings-current-password",
            "autocapitalize": "off",
        },
        validators=[Optional()],
    )
    new_password = PasswordField(
        "New Password",
        render_kw={
            "placeholder": "New Password",
            "id": "profile-settings-password",
            "autocapitalize": "off",
        },
        validators=[
            Optional(),
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
        validators=[Optional()],
    )
    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "id": "submit",
            "class": "profile-settings-submit",
        },
    )


class AccountProfileForm(FlaskForm):
    profile_picture = HiddenField(
        "Profile Picture",
        validators=[Optional()],
        render_kw={
            "id": "hidden-base64-profile-picture",
        },
    )

    biography = TextAreaField(
        "Biography",
        validators=[Optional()],
        render_kw={"id": "profile-settings-bio", "cols": "30", "rows": "10"},
    )

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "id": "submit",
            "class": "profile-settings-submit",
        },
    )
