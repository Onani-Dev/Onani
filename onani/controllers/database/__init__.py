# -*- coding: utf-8 -*-
# Backward-compatibility shim — all logic now lives in onani/services/.
from onani.services import (
    create_avatar,
    create_ban,
    create_comment,
    create_default_tags,
    create_news,
    create_post,
    delete_ban,
    determine_meta_tags,
    get_file_data,
    log_error,
    parse_tags,
    query_posts,
    set_tags,
    upload_post,
    create_user,
)

from .. import db
