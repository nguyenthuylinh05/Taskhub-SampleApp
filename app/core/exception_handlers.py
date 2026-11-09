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