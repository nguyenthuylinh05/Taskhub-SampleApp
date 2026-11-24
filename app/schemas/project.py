"""Project request and response schemas."""

from datetime import datetime

from pydantic import Field, model_validator

from app.core.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)
from app.core.messages import UPDATE_FIELDS_CANNOT_BE_NULL, UPDATE_FIELDS_REQUIRED
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

    @model_validator(mode="after")
    def validate_update_fields(self) -> "ProjectUpdate":
        """Require an update and reject null fields that cannot be cleared."""
        if not self.model_fields_set:
            raise ValueError(UPDATE_FIELDS_REQUIRED)

        if any(
            field_name in self.model_fields_set and getattr(self, field_name) is None
            for field_name in ("name", "status")
        ):
            raise ValueError(UPDATE_FIELDS_CANNOT_BE_NULL)

        return self


class ProjectResponse(BaseSchema):
    """Schema for returning project information."""

    id: int
    workspace_id: int
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
