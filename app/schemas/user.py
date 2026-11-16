"""User request and response schemas."""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core.constants import (
    USER_EMAIL_MAX_LENGTH,
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PASSWORD_MIN_LENGTH,
)
from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class UserCreate(BaseSchema):
    """Schema for creating a user."""

    email: EmailStr = Field(max_length=USER_EMAIL_MAX_LENGTH)
    full_name: str = Field(
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )
    role: UserRole = UserRole.MEMBER

    @field_validator("password", mode="before")
    @classmethod
    def preserve_password(cls, value: object) -> object:
        """Preserve password whitespace instead of stripping it."""
        return value


class UserResponse(BaseSchema):
    """Schema for returning user information."""

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserListResponse(BaseSchema):
    """Paginated user list response."""

    items: list[UserResponse]
    total: int
    page: int
    limit: int


class UserUpdate(BaseSchema):
    """Schema for updating user information."""

    email: EmailStr | None = Field(
        default=None,
        max_length=USER_EMAIL_MAX_LENGTH,
    )
    full_name: str | None = Field(
        default=None,
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    role: UserRole | None = None
    is_active: bool | None = None


class UserProfileUpdate(BaseSchema):
    """Schema for updating the current user's profile."""

    email: EmailStr | None = Field(
        default=None,
        max_length=USER_EMAIL_MAX_LENGTH,
    )
    full_name: str | None = Field(
        default=None,
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )


class ChangePasswordRequest(BaseSchema):
    """Schema for changing the current user's password."""

    current_password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )

    @field_validator("current_password", "new_password", mode="before")
    @classmethod
    def preserve_passwords(cls, value: object) -> object:
        """Preserve password whitespace instead of stripping it."""
        return value
