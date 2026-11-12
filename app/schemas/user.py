from datetime import datetime

from pydantic import EmailStr, Field

from app.core.constants import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_FULL_NAME_MAX_LENGTH,
    USER_FULL_NAME_MIN_LENGTH,
)
from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class UserCreate(BaseSchema):
    email: EmailStr = Field(
        max_length=USER_EMAIL_MAX_LENGTH,
    )
    full_name: str = Field(
        min_length=USER_FULL_NAME_MIN_LENGTH,
        max_length=USER_FULL_NAME_MAX_LENGTH,
    )
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    role: UserRole = UserRole.MEMBER


class UserResponse(BaseSchema):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserListResponse(BaseSchema):
    items: list[UserResponse]
    total: int
    page: int
    limit: int


class UserUpdate(BaseSchema):
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
    current_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
