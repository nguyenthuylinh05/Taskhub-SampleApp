from uuid import uuid4

import pytest
from app.core.database import AsyncSessionLocal
from app.models import Comment, Label, Task, User, Workspace
from app.repositories.comment import CommentRepository
from app.repositories.label import LabelRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository


@pytest.mark.asyncio
async def test_user_repository_crud_and_pagination() -> None:
    """Test user repository CRUD operations and pagination."""

    async with AsyncSessionLocal() as session:
        repository = UserRepository(session)
        user_id: int | None = None

        try:
            # 1. Create a user
            email = f"test-{uuid4().hex}@example.com"

            user = await repository.create(
                {
                    "email": email,
                    "full_name": "Repository Test User",
                    "hashed_password": "test_hashed_password",
                }
            )

            user_id = user.id

            assert user.id is not None
            assert user.email == email
            assert user.full_name == "Repository Test User"

            # 2. Get user by ID
            found_user = await repository.get_by_id(user_id)

            assert found_user is not None
            assert found_user.email == email

            found_user_by_email = await repository.get_by_email(email)
            assert found_user_by_email is not None
            assert found_user_by_email.id == user_id

            # 3. Get all users
            users = await repository.get_all()

            assert any(item.id == user_id for item in users)

            # 4. Test pagination
            limit = 10

            _, total = await repository.get_paginated(
                page=1,
                limit=limit,
            )

            last_page = (total - 1) // limit + 1

            paginated_users, paginated_total = (
                await repository.get_paginated(
                    page=last_page,
                    limit=limit,
                )
            )

            assert paginated_total == total
            assert len(paginated_users) <= limit
            assert any(item.id == user_id for item in paginated_users)

            # 5. Update user
            updated_user = await repository.update(
                user_id,
                {"full_name": "Updated Repository Test User"},
            )

            assert updated_user is not None
            assert updated_user.full_name == "Updated Repository Test User"

            # 6. Delete user
            deleted = await repository.delete(user_id)

            assert deleted is True

            deleted_user = await repository.get_by_id(user_id)

            assert deleted_user is None

        finally:
            # Clean up test data if an assertion fails
            if user_id is not None:
                existing_user = await repository.get_by_id(user_id)

                if existing_user is not None:
                    await repository.delete(user_id)


@pytest.mark.asyncio
async def test_repository_initialization() -> None:
    """Test repository initialization with an async session."""

    async with AsyncSessionLocal() as session:
        repositories = [
            (UserRepository(session), User),
            (WorkspaceRepository(session), Workspace),
            (TaskRepository(session), Task),
            (LabelRepository(session), Label),
            (CommentRepository(session), Comment),
        ]

        for repository, expected_model in repositories:
            assert repository.session is session
            assert repository.model is expected_model
