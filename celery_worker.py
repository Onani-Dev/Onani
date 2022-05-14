# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-14 07:16:09
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-14 07:30:18

from Onani import init_app, make_celery
from Onani.tasks import *

app = init_app()
celery = make_celery(app)
