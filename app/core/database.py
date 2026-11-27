from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

CACHE_PROJECT_IDS_INFO_KEY = "task_list_cache_project_ids"


def register_project_cache_invalidation(
    session: AsyncSession,
    project_id: int,
) -> None:
    """Register a project cache version bump for after a successful commit."""

    project_ids = session.info.setdefault(CACHE_PROJECT_IDS_INFO_KEY, set())
    project_ids.add(project_id)


async def invalidate_registered_project_cache_versions(
    session: AsyncSession,
) -> None:
    """Increment project cache versions after the database commit succeeds."""

    from app.core.redis import increment_task_list_cache_version

    project_ids = session.info.pop(CACHE_PROJECT_IDS_INFO_KEY, set())
    for project_id in project_ids:
        await increment_task_list_cache_version(project_id)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide one transaction-scoped database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
            await invalidate_registered_project_cache_versions(session)
        except Exception:
            await session.rollback()
            raise
