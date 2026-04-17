# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-13 00:59:27
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-20 16:15:01
import html
from typing import Dict

import regex as re
from sqlalchemy.orm import validates

from . import db


class UserSettings(db.Model):
    """
    UserSettings Models
    """

    __tablename__ = "settings"
    CONNECTION_REGEX = {
        "deviantart": r"^https:\/\/www\.deviantart\.com\/[.\S]{1,}",
        "discord": r"^[.\S]{1,32}#[\d]{4}",
        "github": r"^https:\/\/github\.com\/[.\S]{1,}",
        "patreon": r"^https:\/\/www\.patreon\.com\/[.\S]{1,}(?:\/)?(?:posts)?",
        "paypal": r"^https:\/\/(paypal\.me|www\.paypal\.com\/paypalme)\/[.\S]{1,}",
        "pixiv": r"^https:\/\/www\.pixiv\.net(?:\/[.\S]{2,4})?\/users\/[\d\S]{1,}",
        "twitter": r"(?:^https:\/\/twitter\.com\/[\w]{1,15}|^@(\w){1,15})",
    }

    id: int = db.Column(db.Integer, primary_key=True)

    # The User that the settings belong to.
    user: int = db.Column(db.Integer, db.ForeignKey("users.id"))

    # User biography. allows custom text on the profile. (and hopefully not Cross Site Scripting)
    biography: str = db.Column(db.UnicodeText)

    # The link to the user's avatar.
    avatar: str = db.Column(db.String)

    # The user's custom css. overrides the default css that i worked so hard on :(
    custom_css: str = db.Column(db.UnicodeText)

    # Custom colour for user profile
    profile_colour: str = db.Column(db.String)

    # SFW mode: blurs explicit/questionable post thumbnails
    sfw_mode: bool = db.Column(db.Boolean, default=False, nullable=False, server_default="false")

    # Encrypted gallery-dl cookies file (Fernet token, encrypted with user password)
    encrypted_cookies: bytes = db.Column(db.LargeBinary)

    # Salt used for PBKDF2 key derivation for the cookies encryption
    cookies_salt: bytes = db.Column(db.LargeBinary)

    # The user's connections to other website's accounts
    connections: Dict = db.Column(
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
        if not biography:
            return None
        if len(biography) > 5120:
            raise ValueError("Biography is too large. (Max 5120)")
        return html.escape(biography)

    @validates("connections")
    def validate_connections(self, key, connections):
        for c in list(connections.keys()):
            if not connections[c]:
                connections[c] = None
                continue
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
        if not css:
            return None
        return html.escape(css)
