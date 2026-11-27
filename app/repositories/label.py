from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    """Repository for label database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Label)
