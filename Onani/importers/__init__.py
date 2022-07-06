# -*- coding: utf-8 -*-
# @Author: Mattlau04
# @Date:   2022-05-01 01:34:41
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-06 09:21:35

from .. import db

from ._importedpost import ImportedPost
from ._baseimporter import BaseImporter, IMPORTERS
from ._utils import find_importer, get_post, save_imported_post

# All importers need to be imported so they're initialised
from . import rule34, danbooru, gelbooru, shimmie2

# EXAMPLE:
# print(get_post("https://rule34.xxx/index.php?page=post&s=view&id=6021167"))
