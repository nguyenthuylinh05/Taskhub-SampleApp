"""Generic asynchronous repository for SQLAlchemy models."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[ModelType: Base]:
    """Generic asynchronous repository for SQLAlchemy models."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ) -> None:
        self.session = session
        self.model = model

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create and return a new database record."""
        db_obj = self.model(**data)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)

        return db_obj

    async def get_by_id(self, obj_id: int) -> ModelType | None:
        """Get a database record by its primary key."""
        return await self.session.get(self.model, obj_id)

    async def get_all(self) -> list[ModelType]:
        """Get all database records."""
        result = await self.session.scalars(select(self.model))
        return list(result.all())

    async def get_paginated(
        self,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[ModelType], int]:
        """Get paginated records and the total record count."""
        if page < 1:
            raise ValueError("Page must be greater than or equal to 1")
        if limit < 1:
            raise ValueError("Limit must be greater than or equal to 1")

        total_result = await self.session.scalar(
            select(func.count()).select_from(self.model)
        )
        total = total_result or 0

        statement = (
            select(self.model)
            .order_by(*self.model.__mapper__.primary_key)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.session.scalars(statement)

        return list(result.all()), total

    async def update(
        self,
        obj_id: int,
        data: dict[str, Any],
    ) -> ModelType | None:
        """Update a database record by its primary key."""
        db_obj = await self.get_by_id(obj_id)

        if db_obj is None:
            return None

        for key, value in data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        await self.session.flush()
        await self.session.refresh(db_obj)

        return db_obj

    async def delete(self, obj_id: int) -> bool:
        """Delete a database record by its primary key."""
        db_obj = await self.get_by_id(obj_id)

        if db_obj is None:
            return False

        await self.session.delete(db_obj)
        await self.session.flush()

        return True
