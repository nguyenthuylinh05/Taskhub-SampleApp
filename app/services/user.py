from typing import Any, NoReturn

from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core import messages
from app.core.db_errors import is_email_unique_violation
from app.core.exceptions import (
    AppException,
    CannotDeleteOwnAccount,
    ConflictError,
    EmailAlreadyRegistered,
    NotFoundException,
)
from app.core.security import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)


class UserService:
    """Business logic for user management."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_update_data(data: dict[str, Any]) -> None:
        """Validate partial user updates."""

        if not data:
            raise AppException(
                messages.UPDATE_FIELDS_REQUIRED,
                status_code=422,
            )

        if any(value is None for value in data.values()):
            raise AppException(
                messages.UPDATE_FIELDS_CANNOT_BE_NULL,
                status_code=422,
            )

    async def _check_email_available(
        self,
        email: str,
        exclude_user_id: int | None = None,
    ) -> None:
        """Ensure an email is not already assigned to another user."""

        existing_user = await self.repository.get_by_email(email)

        if existing_user is not None and existing_user.id != exclude_user_id:
            raise EmailAlreadyRegistered()

    @staticmethod
    def _handle_email_integrity_error(exc: IntegrityError) -> NoReturn:
        """Translate duplicate-email database errors into a domain error."""

        if is_email_unique_violation(exc):
            raise EmailAlreadyRegistered() from None

        raise exc

    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
    ) -> UserListResponse:
        """Get a paginated list of users."""

        users, total = await self.repository.get_paginated(
            page=page,
            limit=limit,
        )

        return UserListResponse(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_user(self, user_id: int) -> UserResponse:
        """Get a user by ID."""

        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        return UserResponse.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Create a user and hash the supplied password."""

        email = str(data.email)
        await self._check_email_available(email)

        hashed_password = await run_in_threadpool(
            hash_password,
            data.password,
        )

        user_data = data.model_dump(exclude={"password"})
        user_data["email"] = email
        user_data["hashed_password"] = hashed_password

        try:
            user = await self.repository.create_user(user_data)
        except ConflictError as exc:
            if exc.message == messages.EMAIL_ALREADY_REGISTERED:
                raise EmailAlreadyRegistered() from None
            raise

        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: int,
        data: UserUpdate,
    ) -> UserResponse:
        """Update an administrative user profile."""

        update_data = data.model_dump(exclude_unset=True)
        self._validate_update_data(update_data)

        if "email" in update_data:
            update_data["email"] = str(update_data["email"])
            await self._check_email_available(
                update_data["email"],
                exclude_user_id=user_id,
            )

        try:
            user = await self.repository.update_user(
                user_id,
                update_data,
            )
        except IntegrityError as exc:
            self._handle_email_integrity_error(exc)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        return UserResponse.model_validate(user)

    async def update_profile(
        self,
        user_id: int,
        data: UserProfileUpdate,
    ) -> UserResponse:
        """Update the authenticated user's own profile."""

        update_data = data.model_dump(exclude_unset=True)
        self._validate_update_data(update_data)

        if "email" in update_data:
            update_data["email"] = str(update_data["email"])
            await self._check_email_available(
                update_data["email"],
                exclude_user_id=user_id,
            )

        try:
            user = await self.repository.update(
                user_id,
                update_data,
            )
        except IntegrityError as exc:
            self._handle_email_integrity_error(exc)

        if user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

        return UserResponse.model_validate(user)

    async def delete_user(
        self,
        user_id: int,
        requester_id: int,
    ) -> None:
        """Delete a user while enforcing account-management rules."""

        if user_id == requester_id:
            raise CannotDeleteOwnAccount()

        deleted = await self.repository.delete_user(user_id)

        if not deleted:
            raise NotFoundException(messages.USER_NOT_FOUND)
