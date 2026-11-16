from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import (
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PASSWORD_MIN_LENGTH,
)


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    full_name: str = Field(
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("email", "full_name", mode="before")
    @classmethod
    def strip_user_text_fields(cls, value: object) -> object:
        """Strip whitespace without modifying the password."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("String must not be empty or whitespace only.")
        return value


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: object) -> object:
        """Strip whitespace from email."""
        if isinstance(value, str):
            value = value.strip()
        return value


class TokenResponse(BaseModel):
    """Response schema containing access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request schema for refreshing tokens."""

    refresh_token: str
