"""Comment request and response schemas."""

from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.base import BaseSchema


class CommentCreate(BaseSchema):
    """Schema for creating a task comment."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    content: str = Field(min_length=1, description="Comment text")


class CommentResponse(BaseSchema):
    """Schema for returning comment information."""

    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
