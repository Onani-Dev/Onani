# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-05-02 01:41:39
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-07-27 15:01:44

from typing import Optional

from celery import shared_task

from . import db


@shared_task
def import_post(post_url: str, importer_id: int) -> Optional[str]:
    from Onani.importers import get_post, save_imported_post, ImportedPostSchema

    imported_post = get_post(post_url)

    post = save_imported_post(imported_post, importer_id)

    return ImportedPostSchema().dump(imported_post)
