import asyncio
from uuid import uuid4

import pytest
from app.core.config import settings
from app.core.exceptions import ConflictError
from app.models import User, UserRole
from app.repositories.user import UserRepository
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


@pytest.mark.asyncio
async def test_concurrent_admin_demotion_preserves_one_active_admin() -> None:
    """Concurrent demotions must never remove the last active admin."""

    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    admin_ids: list[int] = []
    test_id = uuid4().hex

    try:
        # Arrange: create exactly two active administrators.
        async with session_factory() as session:
            repository = UserRepository(session)

            first_admin = await repository.create_user(
                {
                    "email": f"admin-concurrency-1-{test_id}@example.test",
                    "full_name": "Concurrency Admin One",
                    "hashed_password": "test-hashed-password",
                    "role": UserRole.ADMIN,
                    "is_active": True,
                }
            )
            admin_ids.append(first_admin.id)

            second_admin = await repository.create_user(
                {
                    "email": f"admin-concurrency-2-{test_id}@example.test",
                    "full_name": "Concurrency Admin Two",
                    "hashed_password": "test-hashed-password",
                    "role": UserRole.ADMIN,
                    "is_active": True,
                }
            )
            admin_ids.append(second_admin.id)

            await session.commit()

        # Synchronize both operations so they start concurrently.
        start_event = asyncio.Event()

        async def demote_admin(user_id: int) -> str:
            async with session_factory() as session:
                repository = UserRepository(session)

                await start_event.wait()

                try:
                    updated_user = await repository.update_user(
                        user_id,
                        {"role": UserRole.MEMBER},
                    )

                    assert updated_user is not None

                    await session.commit()
                    return "updated"

                except ConflictError:
                    await session.rollback()
                    return "protected"

        first_task = asyncio.create_task(demote_admin(first_admin.id))
        second_task = asyncio.create_task(demote_admin(second_admin.id))

        # Release both operations at the same time.
        start_event.set()

        outcomes = await asyncio.gather(
            first_task,
            second_task,
        )

        # Exactly one operation must succeed.
        assert outcomes.count("updated") == 1
        assert outcomes.count("protected") == 1

        # The database must still contain one active administrator.
        async with session_factory() as session:
            repository = UserRepository(session)

            active_admin_count = await repository.count_active_admins()

            assert active_admin_count == 1

    finally:
        # Remove only the test users.
        # Direct SQL cleanup intentionally bypasses the last-admin guard.
        if admin_ids:
            async with session_factory() as session:
                await session.execute(delete(User).where(User.id.in_(admin_ids)))
                await session.commit()

        await engine.dispose()
