import pytest
from app.models import Comment, Label, Task, User, Workspace
from app.repositories.comment import CommentRepository
from app.repositories.label import LabelRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_user_repository_crud_and_pagination(
    db_session: AsyncSession,
) -> None:
    """Test user repository CRUD operations and pagination."""

    repository = UserRepository(db_session)

    email = "repository-test@example.com"

    user = await repository.create(
        {
            "email": email,
            "full_name": "Repository Test User",
            "hashed_password": "test_hashed_password",
        }
    )

    assert user.id is not None
    assert user.email == email
    assert user.full_name == "Repository Test User"

    found_user = await repository.get_by_id(user.id)

    assert found_user is not None
    assert found_user.email == email

    found_user_by_email = await repository.get_by_email(email)

    assert found_user_by_email is not None
    assert found_user_by_email.id == user.id

    users = await repository.get_all()

    assert any(item.id == user.id for item in users)

    first_page_users, total = await repository.get_paginated(
        page=1,
        limit=10,
    )

    assert total >= 1
    assert len(first_page_users) <= 10

    last_page = (total - 1) // 10 + 1

    last_page_users, last_page_total = await repository.get_paginated(
        page=last_page,
        limit=10,
    )

    assert last_page_total == total
    assert len(last_page_users) <= 10
    assert any(item.id == user.id for item in last_page_users)

    updated_user = await repository.update(
        user.id,
        {"full_name": "Updated Repository Test User"},
    )

    assert updated_user is not None
    assert updated_user.full_name == "Updated Repository Test User"

    deleted = await repository.delete(user.id)

    assert deleted is True

    deleted_user = await repository.get_by_id(user.id)

    assert deleted_user is None


@pytest.mark.asyncio
async def test_repository_initialization(
    db_session: AsyncSession,
) -> None:
    """Test repository initialization with an async session."""

    repositories = [
        (UserRepository(db_session), User),
        (WorkspaceRepository(db_session), Workspace),
        (TaskRepository(db_session), Task),
        (LabelRepository(db_session), Label),
        (CommentRepository(db_session), Comment),
    ]

    for repository, expected_model in repositories:
        assert repository.session is db_session
        assert repository.model is expected_model
