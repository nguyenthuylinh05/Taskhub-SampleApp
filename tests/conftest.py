"""Shared fixtures for database and API tests."""

import os
from collections.abc import AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock
from uuid import uuid4

import anyio
import pytest
import pytest_asyncio
import redis.asyncio as redis
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.core.database import get_db_session
from app.main import app
from app.models import User, Workspace
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


@pytest.fixture
def register_and_login(
    client: TestClient,
    cleanup_user: list[int],
) -> Callable[[], tuple[int, dict[str, str]]]:
    """Register a test user and return its ID and authentication headers."""

    def _register_and_login() -> tuple[int, dict[str, str]]:
        email = f"test_{uuid4().hex[:12]}@example.com"

        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Test User",
                "password": "TestPassword123",
            },
        )
        assert register_response.status_code == 201

        user_id = register_response.json()["id"]
        cleanup_user.append(user_id)

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "TestPassword123",
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        return user_id, {"Authorization": f"Bearer {token}"}

    return _register_and_login


@pytest.fixture
def create_test_workspace(
    client: TestClient,
    cleanup_workspace: list[int],
) -> Callable[[dict[str, str]], int]:
    """Create a test workspace and register it for cleanup."""

    def _create_test_workspace(headers: dict[str, str]) -> int:
        response = client.post(
            "/api/v1/workspaces",
            headers=headers,
            json={"name": "Test Workspace"},
        )
        assert response.status_code == 201

        workspace_id = response.json()["id"]
        assert isinstance(workspace_id, int)

        cleanup_workspace.append(workspace_id)
        return workspace_id

    return _create_test_workspace


@pytest.fixture(scope="session")
def migrated_test_database() -> None:
    """Apply Alembic migrations to the dedicated test database."""

    if settings.POSTGRES_TEST_DB == settings.POSTGRES_DB:
        raise RuntimeError(
            "Test database must be different from the development database."
        )

    test_database_url = settings.TEST_DATABASE_URL.render_as_string(
        hide_password=False,
    )

    previous_url = os.environ.get("TASKHUB_DATABASE_URL")
    os.environ["TASKHUB_DATABASE_URL"] = test_database_url

    try:
        alembic_config = Config("alembic.ini")
        command.upgrade(alembic_config, "head")
    finally:
        if previous_url is None:
            os.environ.pop("TASKHUB_DATABASE_URL", None)
        else:
            os.environ["TASKHUB_DATABASE_URL"] = previous_url


@pytest_asyncio.fixture
async def db_session(
    migrated_test_database: None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transaction-isolated test database session."""

    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            session = AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )

            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest.fixture
def mock_redis(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    """Mock Redis operations used by authentication and user endpoints."""

    store_mock = AsyncMock()
    rotate_mock = AsyncMock(return_value=True)
    revoke_mock = AsyncMock(return_value=True)
    revoke_all_mock = AsyncMock(return_value=2)

    monkeypatch.setattr(
        "app.services.auth.store_refresh_token",
        store_mock,
    )
    monkeypatch.setattr(
        "app.services.auth.rotate_refresh_token",
        rotate_mock,
    )
    monkeypatch.setattr(
        "app.services.auth.revoke_refresh_token",
        revoke_mock,
    )
    monkeypatch.setattr(
        "app.services.auth.revoke_all_refresh_tokens",
        revoke_all_mock,
    )

    return {
        "store": store_mock,
        "rotate": rotate_mock,
        "revoke": revoke_mock,
        "revoke_all": revoke_all_mock,
    }


@pytest_asyncio.fixture
async def real_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[redis.Redis, None]:
    """Provide an isolated Redis DB 15 client for integration tests."""

    import app.core.redis as redis_module

    client = redis.from_url(
        "redis://localhost:6379/15",
        encoding="utf-8",
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
    )

    await client.ping()

    monkeypatch.setattr(
        redis_module,
        "redis_client",
        client,
    )

    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
def client(
    migrated_test_database: None,
    mock_redis: dict[str, AsyncMock],
) -> Generator[TestClient, None, None]:
    """Create an API test client connected to the test database."""

    test_engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        anyio.run(test_engine.dispose)


@pytest.fixture
def cleanup_user() -> Generator[list[int], None, None]:
    """Track user IDs and remove them from the test database."""

    user_ids: list[int] = []
    yield user_ids

    if not user_ids:
        return

    async def delete_test_users() -> None:
        engine = create_async_engine(
            settings.TEST_DATABASE_URL,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        try:
            async with session_factory() as session:
                await session.execute(
                    delete(User).where(User.id.in_(user_ids)),
                )
                await session.commit()
        finally:
            await engine.dispose()

    anyio.run(delete_test_users)


@pytest.fixture
def cleanup_workspace(
    cleanup_user: list[int],
) -> Generator[list[int], None, None]:
    """Track workspace IDs and remove them before cleaning up users."""

    workspace_ids: list[int] = []
    yield workspace_ids

    if not workspace_ids:
        return

    async def delete_test_workspaces() -> None:
        engine = create_async_engine(
            settings.TEST_DATABASE_URL,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        try:
            async with session_factory() as session:
                await session.execute(
                    delete(Workspace).where(
                        Workspace.id.in_(workspace_ids),
                    ),
                )
                await session.commit()
        finally:
            await engine.dispose()

    anyio.run(delete_test_workspaces)
