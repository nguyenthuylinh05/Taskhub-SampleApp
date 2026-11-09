from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Schema for creating a project."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Project name",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Project description",
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class ProjectResponse(BaseModel):
    """Schema for returning project information."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
