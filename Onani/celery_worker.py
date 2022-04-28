# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 01:40:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-29 02:12:50

from . import init_app

from .tasks import *

app = init_app()

from . import celery
