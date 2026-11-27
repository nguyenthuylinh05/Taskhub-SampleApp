"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exception_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
)
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.core.redis import close_redis_connection
from app.middleware.request_logging import RequestLoggingMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    configure_logging(settings.LOG_LEVEL)

    try:
        yield
    finally:
        try:
            await close_redis_connection()
        except Exception:
            logging.getLogger("taskhub.cache").exception("Redis shutdown failed")
            raise
        finally:
            await engine.dispose()


app = FastAPI(
    title="TaskHub — Task Management API",
    description=(
        "TaskHub provides JWT-authenticated task management across workspaces. "
        "Protected endpoints use a Bearer access token. Task lists support "
        "filtering, pagination, search, and Redis caching. Assignment emails "
        "are sent in the background when enabled and configured."
    ),
    version=settings.APP_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Account registration and token lifecycle.",
        },
        {
            "name": "Users",
            "description": "Current profile and administrator user management.",
        },
        {
            "name": "Workspaces",
            "description": "Workspace and member management.",
        },
        {"name": "Projects", "description": "Projects scoped to a workspace."},
        {
            "name": "Tasks",
            "description": "Task lifecycle, assignment, filtering, and pagination.",
        },
        {
            "name": "Labels",
            "description": "Project labels and task-label associations.",
        },
        {
            "name": "Comments",
            "description": "Task comments and author/owner permissions.",
        },
        {"name": "Health", "description": "Application health status."},
    ],
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(
    AppException,
    app_exception_handler,
)
app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get(
    "/health",
    tags=["Health"],
)
async def health_check() -> dict[str, str]:
    """Return application health status."""

    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
