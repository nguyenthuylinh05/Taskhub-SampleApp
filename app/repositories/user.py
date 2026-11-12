from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.db_errors import is_email_unique_violation
from app.core.exceptions import ConflictError
from app.models import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    ADMIN_LOCK_KEY = 74201

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return await self.session.scalar(statement)

    async def lock_admin_operations(self) -> None:
        """Serialize operations that can change active admin membership."""
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": self.ADMIN_LOCK_KEY},
        )

    async def count_active_admins(self) -> int:
        statement = (
            select(func.count())
            .select_from(User)
            .where(
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
            )
        )

        result = await self.session.scalar(statement)
        return result or 0

    async def create_user(self, data: dict[str, Any]) -> User:
        """Create a user, serializing admin creation with admin changes."""
        role = UserRole(data.get("role", UserRole.MEMBER))

        if role == UserRole.ADMIN:
            await self.lock_admin_operations()

        user = self.model(**data)
        self.session.add(user)

        try:
            await self.session.flush()
            await self.session.refresh(user)
        except IntegrityError as exc:
            if is_email_unique_violation(exc):
                raise ConflictError(messages.EMAIL_ALREADY_REGISTERED) from exc
            raise

        return user

    async def update_user(
        self,
        user_id: int,
        data: dict[str, Any],
    ) -> User | None:
        """Update a user while protecting the last active admin."""
        changes_admin_access = "role" in data or "is_active" in data

        if changes_admin_access:
            await self.lock_admin_operations()

        statement = (
            select(User)
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        user = await self.session.scalar(statement)

        if user is None:
            return None

        removes_admin_access = (
            user.role == UserRole.ADMIN
            and user.is_active
            and (data.get("role") == UserRole.MEMBER or data.get("is_active") is False)
        )

        if removes_admin_access and await self.count_active_admins() <= 1:
            raise ConflictError(messages.CANNOT_REMOVE_LAST_ACTIVE_ADMIN)

        for key, value in data.items():
            setattr(user, key, value)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user while protecting the last active admin."""
        await self.lock_admin_operations()

        statement = (
            select(User)
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        user = await self.session.scalar(statement)

        if user is None:
            return False

        if (
            user.role == UserRole.ADMIN
            and user.is_active
            and await self.count_active_admins() <= 1
        ):
            raise ConflictError(messages.CANNOT_DELETE_LAST_ACTIVE_ADMIN)

        try:
            await self.session.delete(user)
            await self.session.flush()
        except IntegrityError as exc:
            raise ConflictError(messages.CANNOT_DELETE_REFERENCED_RESOURCE) from exc

        return True
