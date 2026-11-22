"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exception_handlers import app_exception_handler
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    configure_logging(settings.LOG_LEVEL)

    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Task Management API built with FastAPI",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(
    AppException,
    app_exception_handler,
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
