from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""

        statement = select(User).where(User.email == email)
        result = await self.session.scalar(statement)
        return result

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""

        statement = select(User).where(User.id == user_id)
        result = await self.session.scalar(statement)
        return result

    async def count_active_admins(self) -> int:
        """Count active admin users."""
        from app.models.enums import UserRole

        statement = select(func.count()).select_from(User).where(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
        )

        result = await self.session.scalar(statement)
        return result or 0