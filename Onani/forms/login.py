# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-07 01:15:34
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 01:21:24

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField


class LoginForm(FlaskForm):
    username = StringField("Username")
    password = PasswordField("Password")
