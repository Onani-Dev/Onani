# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-07 01:15:34
# @Last Modified by:   Mattlau04
# @Last Modified time: 2023-02-04 14:35:07

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Username",
            "autocapitalize": "off",
        },
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Password",
            "autocapitalize": "off",
        },
    )

    otp_code = IntegerField(
        "OTP Code (leave empty if you didn't enable it)",
        validators=[Optional()],
        render_kw={
            "placeholder": "code",
        },
    )

    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Login",
        },
    )
