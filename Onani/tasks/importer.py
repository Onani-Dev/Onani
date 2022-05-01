# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-02 01:41:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-05-02 01:58:30

from typing import Optional
from celery import shared_task

from . import db


@shared_task
def import_post(post_url: str) -> Optional[str]:
    from Onani.importers import get_post

    return str(get_post(post_url))
