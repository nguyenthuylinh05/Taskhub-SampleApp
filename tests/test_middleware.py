"""Tests for HTTP request logging middleware."""

import logging

import pytest
from app.middleware.request_logging import RequestLoggingMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.types import Receive, Scope, Send


def test_successful_request_is_logged(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A successful request should produce an INFO log."""

    caplog.set_level(logging.INFO, logger="taskhub.request")

    response = client.get(
        "/health",
        headers={"X-Request-ID": "test-request-123"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-123"

    records = [
        record
        for record in caplog.records
        if record.name == "taskhub.request"
    ]

    assert any(
        "HTTP GET /health completed with status 200" in record.message
        and "request_id=test-request-123" in record.message
        and record.levelno == logging.INFO
        for record in records
    )


def test_not_found_request_is_logged_as_warning(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A 404 response should produce a WARNING log."""

    caplog.set_level(logging.INFO, logger="taskhub.request")

    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404

    assert any(
        record.levelno == logging.WARNING
        and "status 404" in record.message
        for record in caplog.records
        if record.name == "taskhub.request"
    )


def test_query_string_and_authorization_are_not_logged(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sensitive query parameters and authorization headers must not be logged."""

    caplog.set_level(logging.INFO, logger="taskhub.request")

    secret_query = "query-secret-123"
    secret_token = "token-secret-456"

    response = client.get(
        f"/health?token={secret_query}",
        headers={"Authorization": f"Bearer {secret_token}"},
    )

    assert response.status_code == 200

    messages = [
        record.message
        for record in caplog.records
        if record.name == "taskhub.request"
    ]

    combined_logs = " ".join(messages)

    assert secret_query not in combined_logs
    assert secret_token not in combined_logs
    assert "/health" in combined_logs
    assert "?token=" not in combined_logs


def test_invalid_request_id_is_replaced(
    client: TestClient,
) -> None:
    """An invalid incoming request ID should be replaced."""

    response = client.get(
        "/health",
        headers={"X-Request-ID": "invalid request id\n"},
    )

    assert response.status_code == 200

    request_id = response.headers["x-request-id"]

    assert request_id != "invalid request id\n"
    assert len(request_id) == 32
    assert all(
        character in "0123456789abcdef"
        for character in request_id
    )


def test_unhandled_exception_is_logged_without_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unhandled exceptions should be logged without duplicating tracebacks."""

    test_app = FastAPI()

    @test_app.get("/test-unhandled-exception")
    async def raise_exception() -> None:
        raise RuntimeError("sensitive exception details")

    test_app.add_middleware(RequestLoggingMiddleware)

    caplog.set_level(logging.ERROR, logger="taskhub.request")

    with TestClient(
        test_app,
        raise_server_exceptions=False,
    ) as test_client:
        response = test_client.get("/test-unhandled-exception")

    assert response.status_code == 500

    records = [
        record
        for record in caplog.records
        if record.name == "taskhub.request"
    ]

    assert len(records) == 1

    record = records[0]

    assert record.levelno == logging.ERROR
    assert "failed with status 500" in record.message
    assert "request_id=" in record.message
    assert record.exc_info is None
    assert record.exc_text is None
    assert "sensitive" not in record.message.lower()


def test_service_unavailable_is_logged_as_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A 503 response should produce an ERROR log."""

    async def unavailable_app(
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Service unavailable",
            }
        )

    caplog.set_level(logging.INFO, logger="taskhub.request")

    test_app = RequestLoggingMiddleware(unavailable_app)

    # This test app does not implement ASGI lifespan.
    # Do not use TestClient as a context manager.
    test_client = TestClient(test_app)
    response = test_client.get("/test")

    assert response.status_code == 503

    assert any(
        record.levelno == logging.ERROR
        and "status 503" in record.message
        for record in caplog.records
        if record.name == "taskhub.request"
    )
