from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Workspace
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for workspace database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workspace)
