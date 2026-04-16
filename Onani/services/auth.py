# -*- coding: utf-8 -*-
"""Pure authentication logic — no Flask request/response concerns."""
from datetime import datetime, timezone
from typing import Optional

import humanize

from Onani.models import User


class AuthError(ValueError):
    """Base class for authentication failures."""


class InvalidCredentialsError(AuthError):
    """Raised when username/password or OTP is wrong."""


class BannedError(AuthError):
    """Raised when the user account is banned."""

    def __init__(self, reason: str, expires: Optional[datetime]):
        self.reason = reason
        self.expires = expires
        super().__init__(self._format())

    def _format(self) -> str:
        if self.expires:
            natural = humanize.naturaltime(datetime.now(timezone.utc) - self.expires)
            formatted = self.expires.strftime("%d/%m/%Y %H:%M:%S") + " UTC"
            return f"This account has been banned.\nReason: {self.reason}\nExpires: {natural} ({formatted})"
        return f"This account has been banned.\nReason: {self.reason}\nExpires: Never"


class DeletedAccountError(AuthError):
    """Raised when the user account has been deleted."""


def verify_credentials(
    user: User,
    password: str,
    otp: Optional[int] = None,
) -> None:
    """Verify a user's password (and OTP if enabled).

    Args:
        user: The ``User`` object to authenticate against.
        password: Plaintext password provided by the client.
        otp: Optional TOTP code if the user has 2FA enabled.

    Raises:
        InvalidCredentialsError: If the password or OTP is wrong.
        BannedError: If the account is banned.
        DeletedAccountError: If the account has been soft-deleted.
    """
    if not user.check_password(password):
        raise InvalidCredentialsError("Invalid username or password.")

    if user.otp_enabled:
        if otp is None or not user.check_otp(otp):
            raise InvalidCredentialsError("Invalid OTP code.")

    if user.is_deleted:
        raise DeletedAccountError("This user account has been deleted.")

    if user.ban:
        raise BannedError(reason=user.ban.reason, expires=user.ban.expires)
