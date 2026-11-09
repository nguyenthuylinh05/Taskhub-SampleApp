from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for task database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)
