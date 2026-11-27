from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Label, task_labels
from app.repositories.base import BaseRepository
from app.schemas.pagination import Pagination


class LabelRepository(BaseRepository[Label]):
    """Repository for label database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Label)

    async def get_by_project(
        self,
        project_id: int,
        pagination: Pagination,
    ) -> tuple[list[Label], int]:
        """List labels in a project in stable ID order."""

        conditions = [Label.project_id == project_id]
        total = (
            await self.session.scalar(
                select(func.count()).select_from(Label).where(*conditions)
            )
            or 0
        )
        result = await self.session.scalars(
            select(Label)
            .where(*conditions)
            .order_by(Label.id)
            .offset((pagination.page - 1) * pagination.limit)
            .limit(pagination.limit)
        )
        return list(result.all()), total

    async def assign_to_task(self, task_id: int, label_id: int) -> bool:
        """Insert an association unless another request already inserted it."""

        statement = (
            pg_insert(task_labels)
            .values(task_id=task_id, label_id=label_id)
            .on_conflict_do_nothing(
                index_elements=[task_labels.c.task_id, task_labels.c.label_id]
            )
            .returning(task_labels.c.task_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def remove_from_task(self, task_id: int, label_id: int) -> bool:
        """Remove only the association, leaving the label intact."""

        statement = (
            delete(task_labels)
            .where(
                task_labels.c.task_id == task_id,
                task_labels.c.label_id == label_id,
            )
            .returning(task_labels.c.task_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None
