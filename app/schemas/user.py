"""User request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.constants import (
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PASSWORD_MIN_LENGTH,
)
from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    full_name: str = Field(
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )
    role: UserRole = UserRole.MEMBER

    @field_validator("email", "full_name", mode="before")
    @classmethod
    def strip_user_text_fields(cls, value: object) -> object:
        """Strip whitespace from email and full name without changing passwords."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("String must not be empty or whitespace only.")
        return value


class UserResponse(BaseSchema):
    """Schema for returning user information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseSchema):
    """Schema for updating user information."""

    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    role: UserRole | None = None
    is_active: bool | None = None


class UserProfileUpdate(BaseSchema):
    """Schema for updating the current user's profile."""

    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )


class ChangePasswordRequest(BaseModel):
    """Schema for changing the current user's password."""

    current_password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        min_length=USER_PASSWORD_MIN_LENGTH,
        max_length=USER_PASSWORD_MAX_LENGTH,
    )


class UserListResponse(BaseSchema):
    """Paginated user list response."""

    items: list[UserResponse]
    total: int
    page: int
    limit: int
