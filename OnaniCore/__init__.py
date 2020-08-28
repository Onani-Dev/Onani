# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:57
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-08-28 18:16:23

import logging
import platform
import sys

import requests

# Our version info
__version_info__ = (2, 0, 0)
__version__ = ".".join(map(str, __version_info__))

# Our user agent
user_agent = f"Onani-Core/{__version__} Python/{platform.python_version()} Requests/{requests.__version__}"

from .controllers.database import DatabaseController
from .controllers.scrapers import DanBooruScraper, Scraper
from .models import Post, PostFile, Tag, TagType, User, UserPermissions, UserSettings
