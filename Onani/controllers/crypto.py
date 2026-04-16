# -*- coding: utf-8 -*-
"""Encrypt / decrypt cookie files using a key derived from the user's password."""
from __future__ import annotations

import base64
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
