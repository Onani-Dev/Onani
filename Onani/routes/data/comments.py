# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-01 02:16:18
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-01 02:19:36
from flask import redirect, render_template, request
from flask_login import current_user
from Onani.controllers import create_avatar
from Onani.forms import AccountPlatformForm, AccountProfileForm, AccountSettingsForm
from Onani.models import Ban, Post, Tag

from . import db, main


@main.route("/comments/post", methods=["POST"])
def post_comment():
    raise NotImplementedError()
