"""Tests for user service business logic."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.core.exceptions import (
    ConflictError,
    NotFoundException,
    ValidationException,
)
from app.models import Workspace
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import UserService
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


def make_user_data() -> UserCreate:
    """Create unique user data for each test."""
    suffix = uuid4().hex[:8]

    return UserCreate(
        email=f"user_{suffix}@example.com",
        full_name="Test User",
        password="TestPassword123",
    )


@pytest.fixture
def user_service(db_session: AsyncSession) -> UserService:
    """Provide a UserService using the test database session."""
    repository = UserRepository(db_session)
    return UserService(repository)


@pytest.mark.asyncio
async def test_create_user_success(user_service: UserService) -> None:
    """A user can be created successfully."""
    data = make_user_data()

    user = await user_service.create_user(data)

    assert user.id is not None
    assert user.email == str(data.email)
    assert user.full_name == data.full_name
    assert user.hashed_password != data.password


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    user_service: UserService,
) -> None:
    """Creating a user with an existing email raises ConflictError."""
    data = make_user_data()

    await user_service.create_user(data)

    with pytest.raises(ConflictError):
        await user_service.create_user(data)


@pytest.mark.asyncio
async def test_create_user_integrity_error(
    user_service: UserService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database uniqueness race is converted into ConflictError."""
    data = make_user_data()

    monkeypatch.setattr(
        user_service.repository,
        "create",
        AsyncMock(
            side_effect=IntegrityError(
                "INSERT INTO users",
                {},
                Exception("duplicate key"),
            )
        ),
    )

    with pytest.raises(ConflictError):
        await user_service.create_user(data)


@pytest.mark.asyncio
async def test_get_user_success(user_service: UserService) -> None:
    """An existing user can be retrieved."""
    user = await user_service.create_user(make_user_data())

    result = await user_service.get_user(user.id)

    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_user_not_found(user_service: UserService) -> None:
    """Retrieving a nonexistent user raises NotFoundException."""
    with pytest.raises(NotFoundException):
        await user_service.get_user(999999)


@pytest.mark.asyncio
async def test_get_users_pagination(user_service: UserService) -> None:
    """User listing returns records and the total count."""
    await user_service.create_user(make_user_data())
    await user_service.create_user(make_user_data())

    users, total = await user_service.get_users(page=1, limit=10)

    assert len(users) >= 2
    assert total >= 2


@pytest.mark.asyncio
async def test_update_user_success(user_service: UserService) -> None:
    """An existing user's information can be updated."""
    user = await user_service.create_user(make_user_data())
    new_name = "Updated User"

    updated_user = await user_service.update_user(
        user.id,
        UserUpdate(full_name=new_name),
    )

    assert updated_user.id == user.id
    assert updated_user.full_name == new_name


@pytest.mark.asyncio
async def test_update_user_duplicate_email(
    user_service: UserService,
) -> None:
    """Updating to another user's email raises ConflictError."""
    first_user = await user_service.create_user(make_user_data())
    second_user = await user_service.create_user(make_user_data())

    with pytest.raises(ConflictError):
        await user_service.update_user(
            first_user.id,
            UserUpdate(email=second_user.email),
        )


@pytest.mark.asyncio
async def test_update_user_null_field(
    user_service: UserService,
) -> None:
    """Explicitly setting an update field to None is rejected."""
    user = await user_service.create_user(make_user_data())

    with pytest.raises(ValidationException):
        await user_service.update_user(
            user.id,
            UserUpdate(full_name=None),
        )


@pytest.mark.asyncio
async def test_update_user_not_found(user_service: UserService) -> None:
    """Updating a nonexistent user raises NotFoundException."""
    with pytest.raises(NotFoundException):
        await user_service.update_user(
            999999,
            UserUpdate(full_name="Updated User"),
        )


@pytest.mark.asyncio
async def test_delete_user_success(user_service: UserService) -> None:
    """A user without restricted references can be deleted."""
    user = await user_service.create_user(make_user_data())

    await user_service.delete_user(user.id)

    with pytest.raises(NotFoundException):
        await user_service.get_user(user.id)


@pytest.mark.asyncio
async def test_delete_user_with_owned_workspace(
    user_service: UserService,
    db_session: AsyncSession,
) -> None:
    """Deleting a workspace owner raises ConflictError."""
    user = await user_service.create_user(make_user_data())
    user_id = user.id  # Save ID before the transaction can be rolled back.

    workspace = Workspace(
        name="Test Workspace",
        owner_id=user_id,
    )
    db_session.add(workspace)
    await db_session.commit()

    with pytest.raises(ConflictError):
        await user_service.delete_user(user_id)

    # The failed deletion must not remove the user.
    existing_user = await user_service.get_user(user_id)
    assert existing_user.id == user_id
