# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-13 00:59:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-13 01:00:16
import html

import regex as re
from sqlalchemy.orm import validates

from . import db


class UserSettings(db.Model):
    """
    UserSettings Models
    """

    __tablename__ = "settings"
    CONNECTION_REGEX = {
        "deviantart": r"\bhttps:\/\/www\.deviantart\.com\/[.\S]{1,}\b",
        "discord": r"\b[.\S]{1,32}#[\d]{4,}\b",
        "github": r"\bhttps:\/\/github\.com\/[.\S]{1,}\b",
        "patreon": r"\bhttps:\/\/www\.patreon\.com\/[.\S]{1,}(?:\/)?(?:posts)?\b",
        "paypal": r"\bhttps:\/\/(paypal\.me|www\.paypal\.com\/paypalme)\/[.\S]{1,}\b",
        "pixiv": r"\bhttps:\/\/www\.pixiv\.net(?:\/[.\S]{2,4})?\/users\/[\d\S]{1,}\b",
        "twitter": r"\bhttps:\/\/twitter\.com\/[.\S]{1,}\b",
    }

    id = db.Column(db.Integer, primary_key=True)

    # The User that the settings belong to.
    user = db.Column(db.Integer, db.ForeignKey("users.id"))

    # User biography. allows custom text on the profile. (and hopefully not Cross Site Scripting)
    biography = db.Column(db.UnicodeText)

    # The link to the user's avatar.
    avatar = db.Column(db.String)

    # The user's custom css. overrides the default css that i worked so hard on :(
    custom_css = db.Column(db.UnicodeText)

    # The user's connections to other website's accounts
    connections = db.Column(
        db.JSON,
        default={
            "deviantart": None,
            "discord": None,
            "github": None,
            "patreon": None,
            "paypal": None,
            "pixiv": None,
            "twitter": None,
        },
    )

    @validates("biography")
    def validate_biography(self, key, biography):
        if len(biography) > 1024:
            raise ValueError("Biography is too large. (Max 1024)")
        return html.escape(biography)

    @validates("connections")
    def validate_connections(self, key, connections):
        for c in list(connections.keys()):
            if len(connections[c]) > 64:
                raise ValueError(f"{c} connection is too long. (Max 64)")
            if regex := self.CONNECTION_REGEX.get(c):
                if not re.match(regex, connections[c]):
                    raise ValueError(
                        f"{c} connection did not match the required regex."
                    )
            connections[c] = html.escape(connections[c])
        return connections

    @validates("custom_css")
    def validate_custom_css(self, key, css):
        return html.escape(css)
