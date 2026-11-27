"""Global exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


async def app_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle application exceptions globally."""

    if not isinstance(exc, AppException):
        raise exc

    headers = None

    if exc.status_code == 401:
        headers = {"WWW-Authenticate": "Bearer"}

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
        headers=headers,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a safe 500 response with the request's correlation ID."""
    del exc
    request_id = getattr(request.state, "request_id", None)
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )
