"""Project request and response schemas."""

from datetime import datetime

from pydantic import Field, field_validator

from app.core.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)
from app.models.enums import ProjectStatus
from app.schemas.base import BaseSchema


class ProjectCreate(BaseSchema):
    """Schema for creating a project."""

    name: str = Field(
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
        description="Project name",
    )
    description: str | None = Field(
        default=None,
        max_length=PROJECT_DESCRIPTION_MAX_LENGTH,
        description="Project description",
    )


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""

    name: str | None = Field(
        default=None,
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=PROJECT_DESCRIPTION_MAX_LENGTH,
    )
    status: ProjectStatus | None = None

    @field_validator("name", mode="before")
    @classmethod
    def reject_null_name(cls, value: object) -> object:
        """Reject explicitly null project names."""
        if value is None:
            raise ValueError("Project name cannot be null.")
        return value


class ProjectResponse(BaseSchema):
    """Schema for returning project information."""

    id: int
    workspace_id: int
    name: str
    description: str | None
    created_at: datetime
