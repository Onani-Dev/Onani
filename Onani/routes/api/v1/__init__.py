# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-14 07:44:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-08-10 12:51:09
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user
from flask_restful import Api

from .. import csrf, limiter, db

api_v1 = Blueprint("v1", __name__, url_prefix="/v1")


def api_login_required(f):
    """Require login for all API endpoints except auth routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "/auth/" in request.path:
            return f(*args, **kwargs)
        if not current_user.is_authenticated:
            return {"message": "Authentication required."}, 401
        return f(*args, **kwargs)
    return decorated


api = Api(api_v1, decorators=[csrf.exempt, api_login_required])

from .auth import *
from .collections import *
from .comments import *
from .importer import *
from .index import *
from .news import *
from .posts import *
from .profile import *
from .tags import *
from .users import *
from ._admin import *
