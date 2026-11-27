from datetime import datetime

from pydantic import Field, PositiveInt, field_validator

from app.core.constants import (
    WORKSPACE_NAME_MAX_LENGTH,
    WORKSPACE_NAME_MIN_LENGTH,
)
from app.models.enums import WorkspaceRole
from app.schemas.base import BaseSchema


class WorkspaceCreate(BaseSchema):
    name: str = Field(
        min_length=WORKSPACE_NAME_MIN_LENGTH,
        max_length=WORKSPACE_NAME_MAX_LENGTH,
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class WorkspaceUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=WORKSPACE_NAME_MIN_LENGTH,
        max_length=WORKSPACE_NAME_MAX_LENGTH,
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("Workspace name cannot be null")
        return value.strip() if isinstance(value, str) else value


class WorkspaceResponse(BaseSchema):
    id: int
    name: str
    owner_id: int
    created_at: datetime


class WorkspaceListResponse(BaseSchema):
    items: list[WorkspaceResponse]
    total: int
    page: int
    limit: int


class WorkspaceMemberAdd(BaseSchema):
    user_id: PositiveInt
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberResponse(BaseSchema):
    user_id: PositiveInt
    role: WorkspaceRole
