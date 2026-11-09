from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """Repository for comment database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment)
