from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import WorkspaceRole


class WorkspaceCreate(BaseModel):
    """Schema for creating a workspace."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Workspace name",
    )


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Workspace name",
    )

    @model_validator(mode="after")
    def validate_name(self) -> "WorkspaceUpdate":
        """Reject null name when the field is explicitly provided."""

        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Workspace name cannot be null")

        return self


class WorkspaceResponse(BaseModel):
    """Schema for returning workspace information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    created_at: datetime


class WorkspaceMemberAdd(BaseModel):
    """Schema for adding a member to a workspace."""

    user_id: int
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberResponse(BaseModel):
    """Schema for returning workspace member information."""

    user_id: int
    role: WorkspaceRole
