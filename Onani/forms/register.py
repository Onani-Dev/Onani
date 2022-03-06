# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 23:17:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 01:21:30

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length, EqualTo, Optional


class RegistrationForm(FlaskForm):
    username = StringField("Username", [Length(min=4, max=25)])
    email = StringField("Email (Optional)", [Optional()])
    password = PasswordField(
        "Password",
        [DataRequired(), EqualTo("confirm", message="Passwords must match")],
    )
    confirm = PasswordField("Repeat Password")
