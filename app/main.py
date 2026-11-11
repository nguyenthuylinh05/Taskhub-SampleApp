from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import API_V1_PREFIX, APP_NAME, APP_VERSION
from app.core.database import engine
from app.core.exception_handlers import app_exception_handler
from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Task Management API built with FastAPI",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.include_router(
    api_router,
    prefix=API_V1_PREFIX,
)


@app.get(
    "/health",
    tags=["Health"],
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": APP_NAME,
    }
