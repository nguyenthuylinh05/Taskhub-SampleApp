"""Task request and response schemas."""

from datetime import datetime

from pydantic import AwareDatetime, Field, field_validator, model_validator

from app.core.constants import (
    TASK_TITLE_MAX_LENGTH,
    TASK_TITLE_MIN_LENGTH,
)
from app.core.messages import (
    TASK_DUE_DATE_MUST_BE_FUTURE,
    UPDATE_FIELDS_CANNOT_BE_NULL,
    UPDATE_FIELDS_REQUIRED,
)
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.base import BaseSchema


def validate_future_due_date(value: AwareDatetime | None) -> AwareDatetime | None:
    """Reject due dates in the past."""

    if value is not None and value <= datetime.now(value.tzinfo):
        raise ValueError(TASK_DUE_DATE_MUST_BE_FUTURE)

    return value


class TaskCreate(BaseSchema):
    """Schema for creating a task."""

    title: str = Field(
        min_length=TASK_TITLE_MIN_LENGTH,
        max_length=TASK_TITLE_MAX_LENGTH,
        description="Task title",
    )
    description: str | None = Field(
        default=None,
        description="Task description",
    )
    assignee_id: int | None = Field(
        default=None,
        gt=0,
        description="ID of the assigned workspace member",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority",
    )
    due_date: AwareDatetime | None = Field(
        default=None,
        description="Task due date",
    )

    @field_validator("due_date")
    @classmethod
    def validate_due_date(
        cls,
        value: AwareDatetime | None,
    ) -> AwareDatetime | None:
        """Require a future timezone-aware due date."""

        return validate_future_due_date(value)


class TaskUpdate(BaseSchema):
    """Schema for updating a task."""

    title: str | None = Field(
        default=None,
        min_length=TASK_TITLE_MIN_LENGTH,
        max_length=TASK_TITLE_MAX_LENGTH,
    )
    description: str | None = None
    assignee_id: int | None = Field(
        default=None,
        gt=0,
    )
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: AwareDatetime | None = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(
        cls,
        value: AwareDatetime | None,
    ) -> AwareDatetime | None:
        """Require a future timezone-aware due date."""

        return validate_future_due_date(value)

    @model_validator(mode="after")
    def validate_update_fields(self) -> "TaskUpdate":
        """Require at least one field and reject null required fields."""

        if not self.model_fields_set:
            raise ValueError(UPDATE_FIELDS_REQUIRED)

        required_fields = ("title", "status", "priority")

        if any(
            field_name in self.model_fields_set
            and getattr(self, field_name) is None
            for field_name in required_fields
        ):
            raise ValueError(UPDATE_FIELDS_CANNOT_BE_NULL)

        return self


class TaskResponse(BaseSchema):
    """Schema for returning task information."""

    id: int
    project_id: int
    assignee_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    created_by: int
    created_at: datetime


class TaskListResponse(BaseSchema):
    """Paginated task list response."""

    items: list[TaskResponse]
    total: int
    page: int
    limit: int
