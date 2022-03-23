# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-04 15:56:02
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-24 02:18:16

from .. import db
from .database import create_avatar, create_files, create_user, create_default_tags
from .role import role_required


from .uploading import upload_files
