# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:57
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-10 14:12:11

import logging
import platform
import sys
from collections import namedtuple

import requests


# Our version info
VersionInfo = namedtuple("VersionInfo", "major minor patch type")
__version_info__ = VersionInfo(major=1, minor=0, patch=0, type="dev")
__version__ = ".".join(map(str, __version_info__))

# Our user agent
user_agent = f"Onani-Core/{__version__} Python/{platform.python_version()} Requests/{requests.__version__}"


from .controllers.database import DatabaseController
from .controllers.scrapers import DanBooruScraper, Scraper
from .exceptions import *
from .models import (
    Post,
    PostData,
    PostFile,
    PostRating,
    PostStatus,
    Tag,
    TagType,
    User,
    UserPermissions,
    UserSettings,
)
from .utils import *
