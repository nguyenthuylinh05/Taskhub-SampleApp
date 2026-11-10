from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.core.constants import (
    PROJECT_DESCRIPTION_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_NAME_MIN_LENGTH,
)
from app.schemas.base import BaseSchema


class ProjectCreate(BaseSchema):
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
    name: str | None = Field(
        default=None,
        min_length=PROJECT_NAME_MIN_LENGTH,
        max_length=PROJECT_NAME_MAX_LENGTH,
    )
    description: str | None = Field(
        default=None,
        max_length=PROJECT_DESCRIPTION_MAX_LENGTH,
    )

    @field_validator("name", mode="before")
    @classmethod
    def reject_explicit_null_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("Project name cannot be null")
        return value


class ProjectResponse(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime