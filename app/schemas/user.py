"""User request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import (
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PASSWORD_MIN_LENGTH,
)
from app.models.enums import UserRole


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


class UserResponse(BaseModel):
    """Schema for returning user information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    role: UserRole | None = None
    is_active: bool | None = None


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserResponse]
    total: int
    page: int
    limit: int
