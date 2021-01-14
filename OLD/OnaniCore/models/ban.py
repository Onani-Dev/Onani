# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-27 18:39:21
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-09-27 12:36:23

from datetime import datetime

from dateutil import tz

from ..utils import setup_logger

log = setup_logger(__name__)


class Ban(object):
    """
    Onani User Ban object
    """

    __slots__ = ("_db", "user", "reason", "ban_creator", "since", "expires")

    def __init__(
        self, db, user, reason: str, ban_creator, since: datetime, expires: datetime,
    ):
        self._db = db
        self.user = user
        self.reason = reason
        self.ban_creator = ban_creator
        self.since = since.replace(tzinfo=tz.tzutc())
        self.expires = expires.replace(tzinfo=tz.tzutc())

    @property
    def has_expired(self):
        return datetime.utcnow().replace(tzinfo=tz.tzutc()) >= self.expires

    def __repr__(self):
        return f"<Ban(user='{self.user}', reason='{self.reason}', expires='{self.expires}')>"
