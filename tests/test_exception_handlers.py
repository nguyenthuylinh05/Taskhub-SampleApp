"""Tests for global application exception handlers."""

import anyio
from app.core.exception_handlers import app_exception_handler
from app.core.exceptions import (
    AppException,
    InvalidCredentials,
    NotFoundException,
)
from fastapi import Request


def create_test_request() -> Request:
    """Create a minimal request for exception handler tests."""

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "server": ("test", 80),
            "client": ("test", 123),
            "scheme": "http",
            "http_version": "1.1",
            "root_path": "",
        }
    )


def test_app_exception_returns_expected_response() -> None:
    """Application exceptions should preserve status and detail."""

    request = create_test_request()
    exception = AppException("Test application error", 400)

    response = anyio.run(
        app_exception_handler,
        request,
        exception,
    )

    assert response.status_code == 400
    assert response.body == b'{"detail":"Test application error"}'


def test_not_found_exception_returns_404() -> None:
    """NotFoundException should return a 404 response."""

    request = create_test_request()
    exception = NotFoundException("Resource not found")

    response = anyio.run(
        app_exception_handler,
        request,
        exception,
    )

    assert response.status_code == 404
    assert response.body == b'{"detail":"Resource not found"}'


def test_unauthorized_exception_includes_bearer_header() -> None:
    """401 application exceptions should include WWW-Authenticate."""

    request = create_test_request()
    exception = InvalidCredentials()

    response = anyio.run(
        app_exception_handler,
        request,
        exception,
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.body == b'{"detail":"Invalid email or password"}'
