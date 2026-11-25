"""Label request and response schemas."""

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema


class LabelCreate(BaseSchema):
    """Schema for creating a project label."""

    name: str = Field(min_length=1, max_length=255, description="Label name")
    color: str = Field(
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Six-digit hexadecimal color, such as #3366CC",
    )


class LabelUpdate(BaseSchema):
    """Schema for partially updating a label."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @model_validator(mode="after")
    def validate_update(self) -> "LabelUpdate":
        """Require at least one non-null field."""

        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Label fields cannot be null")
        return self


class LabelResponse(BaseSchema):
    """Schema for returning label information."""

    id: int
    project_id: int
    name: str
    color: str
