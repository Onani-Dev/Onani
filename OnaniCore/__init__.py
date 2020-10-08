# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-12 15:52:57
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-10-09 01:07:34

import platform
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
    File,
    Post,
    PostData,
    PostRating,
    PostStatus,
    Tag,
    TagType,
    User,
    UserPermissions,
    UserSettings,
)
from .utils import *
