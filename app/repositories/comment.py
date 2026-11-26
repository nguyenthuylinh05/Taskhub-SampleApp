from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment
from app.repositories.base import BaseRepository
from app.schemas.pagination import Pagination


class CommentRepository(BaseRepository[Comment]):
    """Repository for comment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment)

    async def get_by_task(
        self,
        task_id: int,
        pagination: Pagination,
    ) -> tuple[list[Comment], int]:
        """List comments for a task in creation order."""

        conditions = [Comment.task_id == task_id]
        total = (
            await self.session.scalar(
                select(func.count()).select_from(Comment).where(*conditions)
            )
            or 0
        )
        result = await self.session.scalars(
            select(Comment)
            .where(*conditions)
            .order_by(Comment.created_at, Comment.id)
            .offset((pagination.page - 1) * pagination.limit)
            .limit(pagination.limit)
        )
        return list(result.all()), total
