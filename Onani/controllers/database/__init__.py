# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-06 12:42:57
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-12 13:12:07

from .. import db
from .default import create_default_tags
from .files import create_avatar, create_files
from .posts import create_comment, upload_post
from .users import create_user
from .errors import log_error
