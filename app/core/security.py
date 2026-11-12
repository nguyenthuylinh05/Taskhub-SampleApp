from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.models.enums import TokenType

password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash(
    "dummy-password-for-timing-protection"
)


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plain-text password against its hash."""
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(subject: str) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    expire = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": TokenType.ACCESS,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(UTC)
    expire = now + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS,
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": TokenType.REFRESH,
        "jti": str(uuid4()),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={
            "require": ["sub", "iat", "exp"],
        },
    )

    return payload
