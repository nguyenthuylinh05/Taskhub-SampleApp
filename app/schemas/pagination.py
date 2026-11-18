"""Shared pagination schema."""

from pydantic import BaseModel, Field

from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
)


class Pagination(BaseModel):
    """Common pagination parameters."""

    page: int = Field(
        default=DEFAULT_PAGE,
        ge=1,
        description="Page number",
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Number of items per page",
    )
