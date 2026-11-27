"""Shared fixtures for database tests."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


@pytest.fixture(scope="session")
def migrated_test_database() -> None:
    """Apply Alembic migrations to the dedicated test database."""

    if settings.POSTGRES_TEST_DB == settings.POSTGRES_DB:
        raise RuntimeError(
            "Test database must be different from the development database."
        )

    test_database_url = settings.TEST_DATABASE_URL.render_as_string(hide_password=False)

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
    """Provide an isolated database session for each test."""

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
