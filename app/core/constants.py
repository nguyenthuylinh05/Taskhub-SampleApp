"""Application-wide constants."""

from enum import StrEnum


class TokenType(StrEnum):
    """Supported JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"


# Project
PROJECT_NAME_MIN_LENGTH = 1
PROJECT_NAME_MAX_LENGTH = 100
PROJECT_DESCRIPTION_MAX_LENGTH = 500

# User
USER_FULL_NAME_MIN_LENGTH = 1
USER_FULL_NAME_MAX_LENGTH = 255
USER_PASSWORD_MIN_LENGTH = 8
USER_PASSWORD_MAX_LENGTH = 128

# Authentication
SECONDS_PER_DAY = 24 * 60 * 60