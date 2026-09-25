# -*- coding: utf-8 -*-
"""Encrypt / decrypt gallery-dl cookie files.

Cookies are encrypted with a server key derived from ``SECRET_KEY``. The
password-derived helpers remain only to migrate legacy uploads at login.
"""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_ITERATIONS = 480_000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_cookies(data: bytes, password: str) -> tuple[bytes, bytes]:
    """Encrypt *data* with a key derived from *password*.

    Returns ``(ciphertext, salt)``.
    """
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    token = Fernet(key).encrypt(data)
    return token, salt


def decrypt_cookies(token: bytes, salt: bytes, password: str) -> bytes:
    """Decrypt *token* using a key derived from *password* + *salt*.

    Raises ``cryptography.fernet.InvalidToken`` on wrong password or
    corrupted data.
    """
    key = _derive_key(password, salt)
    return Fernet(key).decrypt(token)


def _server_fernet() -> Fernet:
    from flask import current_app

    digest = hashlib.sha256(b"onani-cookies:" + current_app.config["SECRET_KEY"].encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def server_encrypt(data: bytes) -> bytes:
    """Encrypt *data* with the app's server key (rotating SECRET_KEY invalidates it)."""
    return _server_fernet().encrypt(data)


def server_decrypt(token: bytes) -> bytes:
    """Decrypt a :func:`server_encrypt` token. Raises ``InvalidToken`` on failure."""
    return _server_fernet().decrypt(token)
