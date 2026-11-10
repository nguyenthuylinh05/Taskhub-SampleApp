from collections.abc import AsyncIterator, Generator
from unittest.mock import AsyncMock

import pytest
from app.core.database import get_db_session
from app.main import app
from app.models import User
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


@pytest.fixture
def mock_redis(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    """Mock Redis operations used by AuthService and user endpoints."""
    store_mock = AsyncMock()
    rotate_mock = AsyncMock(return_value=True)
    revoke_mock = AsyncMock(return_value=True)
    revoke_all_mock = AsyncMock(return_value=2)

    monkeypatch.setattr("app.services.auth.store_refresh_token", store_mock)
    monkeypatch.setattr("app.services.auth.rotate_refresh_token", rotate_mock)
    monkeypatch.setattr("app.services.auth.revoke_refresh_token", revoke_mock)
    monkeypatch.setattr(
        "app.api.v1.endpoints.users.revoke_all_refresh_tokens",
        revoke_all_mock,
    )

    return {
        "store": store_mock,
        "rotate": rotate_mock,
        "revoke": revoke_mock,
        "revoke_all": revoke_all_mock,
    }

@pytest.fixture
def client(
    mock_redis: AsyncMock,
) -> Generator[TestClient, None, None]:
    """Create a test client with an isolated database connection pool."""
    from app.core.config import DATABASE_URL

    test_engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()

        import anyio

        anyio.run(test_engine.dispose)


@pytest.fixture
def cleanup_user() -> Generator[list[int], None, None]:
    """Track user IDs and remove them after each test."""
    user_ids: list[int] = []

    yield user_ids

    if not user_ids:
        return

    async def delete_test_users() -> None:
        from app.core.config import DATABASE_URL
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        test_engine = create_async_engine(
            DATABASE_URL,
            poolclass=NullPool,
        )

        session_factory = async_sessionmaker(
            test_engine,
            expire_on_commit=False,
        )

        try:
            async with session_factory() as session:
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                await session.commit()
        finally:
            await test_engine.dispose()

    import anyio

    anyio.run(delete_test_users)
