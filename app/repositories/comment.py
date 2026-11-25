from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """Repository for comment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment)

    async def get_by_task(self, task_id: int) -> list[Comment]:
        """List comments for a task in creation order."""

        result = await self.session.scalars(
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at, Comment.id)
        )
        return list(result.all())
