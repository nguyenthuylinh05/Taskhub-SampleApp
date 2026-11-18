"""Repository for task database operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for task database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    async def get_filtered_by_project(
        self,
        project_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Task], int]:
        """Get filtered and paginated tasks belonging to a project."""

        conditions = [Task.project_id == project_id]

        if status is not None:
            conditions.append(Task.status == status)

        if priority is not None:
            conditions.append(Task.priority == priority)

        if assignee_id is not None:
            conditions.append(Task.assignee_id == assignee_id)

        total_statement = (
            select(func.count())
            .select_from(Task)
            .where(*conditions)
        )
        total = await self.session.scalar(total_statement) or 0

        statement = (
            select(Task)
            .where(*conditions)
            .order_by(Task.id)
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.session.scalars(statement)

        return list(result.all()), total

    async def get_by_project_id(self, project_id: int) -> list[Task]:
        """Get all tasks belonging to a project, ordered by ID."""

        statement = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.id)
        )
        result = await self.session.scalars(statement)

        return list(result.all())

    async def get_in_project(
        self,
        task_id: int,
        project_id: int,
    ) -> Task | None:
        """Get a task only if it belongs to the specified project."""

        statement = select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id,
        )

        return await self.session.scalar(statement)
