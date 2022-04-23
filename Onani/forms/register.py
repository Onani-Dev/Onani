# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 23:17:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-23 15:01:53

from flask_wtf import FlaskForm, RecaptchaField
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        render_kw={
            "placeholder": "Username",
            "autocapitalize": "off",
        },
        validators=[DataRequired(), Length(min=4, max=32)],
    )
    email = StringField(
        "Email",
        render_kw={
            "placeholder": "Email (Optional)",
            "autocapitalize": "off",
        },
        validators=[Optional(), Email()],
    )
    password = PasswordField(
        "Password",
        render_kw={
            "placeholder": "Password",
            "autocapitalize": "off",
        },
        validators=[
            DataRequired(),
            EqualTo("confirm", message="Passwords must match"),
            Length(min=4, max=32),
        ],
    )
    confirm = PasswordField(
        "Repeat Password",
        render_kw={
            "placeholder": "Confirm Password",
            "autocapitalize": "off",
        },
        validators=[DataRequired(), Length(min=4, max=32)],
    )

    recaptcha = RecaptchaField()

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Register",
        },
    )
