# -*- coding: utf-8 -*-
from .. import db
from .exceptions import OnaniApiException
from .role import role_required
from .permissions import permissions_required

# Service-layer re-exports (kept here for backward compatibility)
from Onani.services import (
    create_avatar,
    create_comment,
    create_default_tags,
    create_user,
    upload_post,
    get_file_data,
    determine_meta_tags,
    create_post,
    create_ban,
    delete_ban,
    create_news,
    query_posts,
    parse_tags,
    set_tags,
)
# auth helpers remain in controllers.auth (they are web-layer utilities)
from .auth import user_login
