"""Label request and response schemas."""

from pydantic import Field, model_validator

from app.core.constants import (
    LABEL_COLOR_PATTERN,
    LABEL_NAME_MAX_LENGTH,
    LABEL_NAME_MIN_LENGTH,
)
from app.core.messages import UPDATE_FIELDS_REQUIRED
from app.schemas.base import BaseSchema


class LabelCreate(BaseSchema):
    """Schema for creating a project label."""

    name: str = Field(
        min_length=LABEL_NAME_MIN_LENGTH,
        max_length=LABEL_NAME_MAX_LENGTH,
        description="Label name",
    )
    color: str = Field(
        pattern=LABEL_COLOR_PATTERN,
        description="Six-digit hexadecimal color, such as #3366CC",
    )


class LabelUpdate(BaseSchema):
    """Schema for partially updating a label."""

    name: str | None = Field(
        default=None,
        min_length=LABEL_NAME_MIN_LENGTH,
        max_length=LABEL_NAME_MAX_LENGTH,
    )
    color: str | None = Field(default=None, pattern=LABEL_COLOR_PATTERN)

    @model_validator(mode="after")
    def validate_update(self) -> "LabelUpdate":
        """Require at least one non-null field."""

        if not self.model_fields_set:
            raise ValueError(UPDATE_FIELDS_REQUIRED)
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Label fields cannot be null")
        return self


class LabelResponse(BaseSchema):
    """Schema for returning label information."""

    id: int
    project_id: int
    name: str
    color: str


class LabelListResponse(BaseSchema):
    """Paginated project label list."""

    items: list[LabelResponse]
    total: int
    page: int
    limit: int
