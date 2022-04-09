# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-18 21:17:38
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-10 04:08:40
from flask_wtf import FlaskForm
from Onani.models import UserSettings
from wtforms import HiddenField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp
from wtforms.widgets import ColorInput


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

    profile_colour = StringField(
        "Profile Colour",
        validators=[
            Optional(),
            Regexp(r"^#(?:[0-9a-fA-F]{3}){1,2}$", message="Must be a valid hex code."),
        ],
        render_kw={
            "id": "profile-colour",
        },
        widget=ColorInput(),
    )

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "id": "submit",
            "class": "profile-settings-submit",
        },
    )


class AccountPlatformForm(FlaskForm):
    twitter = StringField(
        "Twitter",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["twitter"])],
        render_kw={
            "placeholder": "Twitter profile link / Nametag",
            "id": "settings-twitter",
            "pattern": UserSettings.CONNECTION_REGEX["twitter"],
            "onkeyup": "this.reportValidity();",
        },
    )
    pixiv = StringField(
        "Pixiv",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["pixiv"])],
        render_kw={
            "placeholder": "Pixiv profile link",
            "id": "settings-pixiv",
            "pattern": UserSettings.CONNECTION_REGEX["pixiv"],
            "onkeyup": "this.reportValidity();",
        },
    )
    patreon = StringField(
        "Patreon",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["patreon"])],
        render_kw={
            "placeholder": "Patreon profile",
            "id": "settings-patreon",
            "pattern": UserSettings.CONNECTION_REGEX["patreon"],
            "onkeyup": "this.reportValidity();",
        },
    )
    deviantart = StringField(
        "DeviantArt",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["deviantart"])],
        render_kw={
            "placeholder": "DeviantArt profile link",
            "id": "settings-deviantart",
            "pattern": UserSettings.CONNECTION_REGEX["deviantart"],
            "onkeyup": "this.reportValidity();",
        },
    )
    discord = StringField(
        "Discord",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["discord"])],
        render_kw={
            "placeholder": "Discord Username#Discriminator",
            "id": "settings-discord",
            "pattern": UserSettings.CONNECTION_REGEX["discord"],
            "onkeyup": "this.reportValidity();",
        },
    )
    github = StringField(
        "GitHub",
        validators=[Optional(), Regexp(UserSettings.CONNECTION_REGEX["github"])],
        render_kw={
            "placeholder": "Github profile link",
            "id": "settings-github",
            "pattern": UserSettings.CONNECTION_REGEX["github"],
            "onkeyup": "this.reportValidity();",
        },
    )
    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Save Changes",
            "id": "submit",
            "class": "profile-settings-submit",
        },
    )
