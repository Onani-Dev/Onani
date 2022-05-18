# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-04-29 01:40:05
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-18 08:23:10

from Onani import init_app

from Onani.tasks import *

app = init_app()

from Onani import celery
