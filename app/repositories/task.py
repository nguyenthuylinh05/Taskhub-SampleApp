"""Repository for task database operations."""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Project, Task
from app.models.enums import TaskPriority, TaskStatus
from app.repositories.base import BaseRepository
from app.schemas.pagination import Pagination


class TaskRepository(BaseRepository[Task]):
    """Repository for task database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    async def get_by_id_with_labels(self, task_id: int) -> Task | None:
        """Get a task and eagerly load its assigned labels."""

        statement = (
            select(Task)
            .options(selectinload(Task.labels))
            .where(Task.id == task_id)
        )
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def get_filtered_by_project(
        self,
        project_id: int,
        pagination: Pagination,
        status: list[TaskStatus] | None = None,
        priority: list[TaskPriority] | None = None,
        assignee_id: int | None = None,
    ) -> tuple[list[Task], int]:
        """Get filtered and paginated tasks belonging to a project."""

        conditions = [Task.project_id == project_id]

        if status:
            conditions.append(Task.status.in_(status))

        if priority:
            conditions.append(Task.priority.in_(priority))

        if assignee_id is not None:
            conditions.append(Task.assignee_id == assignee_id)

        total_statement = select(func.count()).select_from(Task).where(*conditions)
        total = await self.session.scalar(total_statement) or 0

        statement = (
            select(Task)
            .where(*conditions)
            .options(selectinload(Task.labels))
            .order_by(Task.id)
            .offset((pagination.page - 1) * pagination.limit)
            .limit(pagination.limit)
        )

        result = await self.session.scalars(statement)

        return list(result.all()), total

    async def unassign_from_workspace(
        self,
        workspace_id: int,
        user_id: int,
    ) -> None:
        """Unassign a user from tasks in a specific workspace."""

        project_ids = select(Project.id).where(
            Project.workspace_id == workspace_id,
        )

        statement = (
            update(Task)
            .where(
                Task.project_id.in_(project_ids),
                Task.assignee_id == user_id,
            )
            .values(assignee_id=None)
        )

        await self.session.execute(statement)
