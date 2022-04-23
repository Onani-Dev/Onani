# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-07 01:15:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-23 15:02:04

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired


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
    submit = SubmitField(
        "Submit",
        render_kw={
            "value": "Login",
        },
    )
