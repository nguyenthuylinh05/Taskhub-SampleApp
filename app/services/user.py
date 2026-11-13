"""Business logic for user operations."""

from sqlalchemy.exc import IntegrityError

from app.core import messages
from app.core.exceptions import (
    ConflictError,
    NotFoundException,
    ValidationException,
)
from app.core.security import hash_password
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service responsible for user business logic and transactions."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
        self.session = repository.session

    async def create_user(self, data: UserCreate) -> User:
        """Create a user and commit the transaction."""

        existing_user = await self.repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise ConflictError(messages.USER_EMAIL_ALREADY_REGISTERED)

        user_data = data.model_dump(exclude={"password"})
        user_data["email"] = str(data.email)
        user_data["hashed_password"] = hash_password(data.password)

        try:
            user = await self.repository.create(user_data)
            await self.session.commit()
            return user
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(messages.USER_EMAIL_ALREADY_REGISTERED) from exc
        except Exception:
            await self.session.rollback()
            raise

    async def get_user(self, user_id: int) -> User:
        """Get a user by ID."""

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        return user

    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[User], int]:
        """Get users with pagination."""

        return await self.repository.get_paginated(
            page=page,
            limit=limit,
        )

    async def update_user(
        self,
        user_id: int,
        data: UserUpdate,
    ) -> User:
        """Update a user and commit the transaction."""

        update_data = data.model_dump(exclude_unset=True)

        if any(value is None for value in update_data.values()):
            raise ValidationException(messages.USER_UPDATE_FIELDS_CANNOT_BE_NULL)

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        if "email" in update_data:
            update_data["email"] = str(update_data["email"])

            existing_user = await self.repository.get_by_email(update_data["email"])

            if existing_user is not None and existing_user.id != user_id:
                raise ConflictError(messages.USER_EMAIL_ALREADY_REGISTERED)

        try:
            updated_user = await self.repository.update(
                user_id,
                update_data,
            )

            if updated_user is None:
                raise NotFoundException(messages.USER_NOT_FOUND)

            await self.session.commit()
            return updated_user

        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(messages.USER_EMAIL_ALREADY_REGISTERED) from exc
        except Exception:
            await self.session.rollback()
            raise

    async def delete_user(self, user_id: int) -> None:
        """Delete a user while preserving referenced records."""

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        try:
            await self.repository.delete(user_id)
            await self.session.commit()

        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(messages.CANNOT_DELETE_REFERENCED_RESOURCE) from exc
        except Exception:
            await self.session.rollback()
            raise
