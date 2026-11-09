from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.database import engine
from app.core.exception_handlers import app_exception_handler
from app.core.exceptions import AppException
from app.repositories.project import InMemoryProjectRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    app.state.project_repository = InMemoryProjectRepository()

    try:
        yield
    finally:
        await engine.dispose()
        del app.state.project_repository


app = FastAPI(
    title="TaskHub API",
    description="Task Management API built with FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(
    AppException,
    app_exception_handler,
)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get(
    "/health",
    tags=["Health"],
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": "TaskHub",
    }
