"""Tests for HTTP request logging middleware."""

import asyncio
import logging
from collections.abc import AsyncGenerator

import anyio
import pytest
from app.core.exception_handlers import unhandled_exception_handler
from app.core.logging import configure_logging
from app.core.logging_context import request_id_context
from app.middleware import request_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse
from starlette.types import Message, Receive, Scope, Send


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

    records = [record for record in caplog.records if record.name == "taskhub.request"]

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
        record.levelno == logging.WARNING and "status 404" in record.message
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
        record.message for record in caplog.records if record.name == "taskhub.request"
    ]

    combined_logs = " ".join(messages)

    assert secret_query not in combined_logs
    assert secret_token not in combined_logs
    assert "/health" in combined_logs
    assert "?token=" not in combined_logs


@pytest.mark.parametrize(
    ("headers", "expected_request_id"),
    [
        ([], None),
        ([("X-Request-ID", "valid-request-123")], "valid-request-123"),
        ([("X-Request-ID", "invalid request id\n")], None),
        (
            [
                ("X-Request-ID", "first-request-id"),
                ("x-request-id", "second-request-id"),
            ],
            None,
        ),
    ],
    ids=["missing", "valid", "invalid", "duplicate-case-insensitive"],
)
def test_request_id_header_policy(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
    headers: list[tuple[str, str]],
    expected_request_id: str | None,
) -> None:
    """Only one valid incoming request ID is reused."""

    caplog.set_level(logging.INFO, logger="taskhub.request")
    response = client.get("/health", headers=headers)

    assert response.status_code == 200
    request_id = response.headers["x-request-id"]

    if expected_request_id is not None:
        assert request_id == expected_request_id
    else:
        assert request_id not in {value for _, value in headers}
        assert len(request_id) == 32
        assert all(character in "0123456789abcdef" for character in request_id)

    assert response.headers.get_list("x-request-id") == [request_id]
    request_record = next(
        record
        for record in caplog.records
        if record.name == "taskhub.request" and "/health" in record.message
    )
    assert f"request_id={request_id}" in request_record.message


def test_duplicate_request_ids_share_one_canonical_value(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Scope state, response headers, and request logs use one generated ID."""

    observed_scope_ids: list[str] = []
    sent_messages: list[Message] = []

    async def application(scope: Scope, receive: Receive, send: Send) -> None:
        observed_scope_ids.append(scope["state"]["request_id"])
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        sent_messages.append(message)

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/duplicate-request-id",
        "raw_path": b"/duplicate-request-id",
        "query_string": b"",
        "headers": [
            (b"X-Request-ID", b"first-id"),
            (b"x-request-id", b"second-id"),
        ],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }

    caplog.set_level(logging.INFO, logger="taskhub.request")
    anyio.run(
        RequestLoggingMiddleware(application),
        scope,
        receive,
        send,
    )

    canonical_id = observed_scope_ids[0]
    response_ids = [
        value
        for name, value in sent_messages[0]["headers"]
        if name.lower() == b"x-request-id"
    ]
    request_record = next(
        record
        for record in caplog.records
        if record.name == "taskhub.request"
        and "/duplicate-request-id" in record.message
    )

    assert canonical_id not in {"first-id", "second-id"}
    assert response_ids == [canonical_id.encode("ascii")]
    assert f"request_id={canonical_id}" in request_record.message


def test_unhandled_exception_is_logged_without_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unhandled exceptions should be logged without duplicating tracebacks."""

    test_app = FastAPI()

    @test_app.get("/test-unhandled-exception")
    async def raise_exception() -> None:
        raise RuntimeError("sensitive exception details")

    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_exception_handler(Exception, unhandled_exception_handler)

    caplog.set_level(logging.ERROR, logger="taskhub.request")

    with TestClient(
        test_app,
        raise_server_exceptions=False,
    ) as test_client:
        response = test_client.get("/test-unhandled-exception")

    assert response.status_code == 500
    request_id = response.headers["x-request-id"]

    records = [record for record in caplog.records if record.name == "taskhub.request"]

    assert len(records) == 1

    record = records[0]

    assert record.levelno == logging.ERROR
    assert "HTTP GET /test-unhandled-exception failed with status 500" in record.message
    assert f"request_id={request_id}" in record.message
    assert len(request_id) == 32
    assert record.exc_info is None
    assert record.exc_text is None
    assert "sensitive" not in record.message.lower()


def test_request_id_is_available_to_application_logs_and_cleared(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Request IDs flow through app log records and reset after each request."""

    configure_logging("INFO")
    caplog.set_level(logging.WARNING)

    async def application(scope: Scope, receive: Receive, send: Send) -> None:
        assert request_id_context.get() == "trace-123"
        service_logger = logging.getLogger("app.services.example")
        service_logger.disabled = False
        service_logger.warning("service event")
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    async def run_request() -> None:
        middleware = RequestLoggingMiddleware(application)
        scope: Scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/test",
            "raw_path": b"/test",
            "query_string": b"",
            "headers": [(b"x-request-id", b"trace-123")],
            "server": ("test", 80),
            "client": ("test", 123),
            "root_path": "",
        }

        async def receive() -> Message:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: Message) -> None:
            return None

        await middleware(scope, receive, send)
        assert request_id_context.get() is None

    anyio.run(run_request)

    service_record = next(
        record for record in caplog.records if record.name == "app.services.example"
    )
    assert service_record.__dict__["request_id"] == "trace-123"


def test_request_id_context_resets_when_logging_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Logging failures must not leave the current request ID in context."""

    async def application(scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        return None

    def fail_logging(*args: object, **kwargs: object) -> None:
        raise RuntimeError("logging failed")

    monkeypatch.setattr(request_logging.logger, "log", fail_logging)
    outer_token = request_id_context.set("outer-request")
    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [(b"x-request-id", b"inner-request")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }

    try:
        with pytest.raises(RuntimeError, match="logging failed"):
            anyio.run(RequestLoggingMiddleware(application), scope, receive, send)

        assert request_id_context.get() == "outer-request"
    finally:
        request_id_context.reset(outer_token)


def test_cancelled_request_before_response_start_resets_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Cancellation before response start is logged without inventing a status."""

    async def cancelled_app(scope: Scope, receive: Receive, send: Send) -> None:
        raise asyncio.CancelledError

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        return None

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/cancel-before-start",
        "raw_path": b"/cancel-before-start",
        "query_string": b"",
        "headers": [(b"x-request-id", b"cancel-before-start")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }

    caplog.set_level(logging.WARNING, logger="taskhub.request")
    outer_token = request_id_context.set("outer-request")
    try:
        with pytest.raises(asyncio.CancelledError):
            anyio.run(
                RequestLoggingMiddleware(cancelled_app),
                scope,
                receive,
                send,
            )
        assert request_id_context.get() == "outer-request"
    finally:
        request_id_context.reset(outer_token)

    record = next(
        record
        for record in caplog.records
        if record.name == "taskhub.request" and "/cancel-before-start" in record.message
    )
    assert record.levelno == logging.WARNING
    assert "cancelled with status not started" in record.message


def test_cancelled_request_after_response_start_preserves_status_and_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Cancellation after response start retains its status and resets context."""

    sent_messages: list[Message] = []

    async def cancelled_app(scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 202,
                "headers": [],
            }
        )
        raise asyncio.CancelledError

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        sent_messages.append(message)

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/cancel-after-start",
        "raw_path": b"/cancel-after-start",
        "query_string": b"",
        "headers": [(b"x-request-id", b"cancel-after-start")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }

    caplog.set_level(logging.WARNING, logger="taskhub.request")
    outer_token = request_id_context.set("outer-request")
    try:
        with pytest.raises(asyncio.CancelledError):
            anyio.run(
                RequestLoggingMiddleware(cancelled_app),
                scope,
                receive,
                send,
            )
        assert request_id_context.get() == "outer-request"
    finally:
        request_id_context.reset(outer_token)

    assert [message["type"] for message in sent_messages] == ["http.response.start"]
    assert sent_messages[0]["status"] == 202

    record = next(
        record
        for record in caplog.records
        if record.name == "taskhub.request" and "/cancel-after-start" in record.message
    )
    assert record.levelno == logging.WARNING
    assert "cancelled with status 202" in record.message


def test_failed_response_start_is_not_recorded_as_started(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed send of response-start does not claim the response was started."""

    async def application(scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 202,
                "headers": [],
            }
        )

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def fail_send(message: Message) -> None:
        raise RuntimeError("response start send failed")

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/failed-response-start",
        "raw_path": b"/failed-response-start",
        "query_string": b"",
        "headers": [(b"x-request-id", b"failed-response-start")],
        "server": ("test", 80),
        "client": ("test", 123),
        "root_path": "",
    }

    caplog.set_level(logging.ERROR, logger="taskhub.request")
    outer_token = request_id_context.set("outer-request")
    try:
        with pytest.raises(RuntimeError, match="response start send failed"):
            anyio.run(
                RequestLoggingMiddleware(application),
                scope,
                receive,
                fail_send,
            )
        assert request_id_context.get() == "outer-request"
    finally:
        request_id_context.reset(outer_token)

    record = next(
        record
        for record in caplog.records
        if record.name == "taskhub.request"
        and "/failed-response-start" in record.message
    )
    assert "failed with status 500" in record.message
    assert "failed after response start" not in record.message


def test_exception_after_response_start_logs_actual_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A late failure does not claim the server returned status 500."""

    test_app = FastAPI()

    async def failing_body() -> AsyncGenerator[bytes, None]:
        yield b"started"
        raise RuntimeError("failure after response start")

    @test_app.get("/late-failure")
    async def late_failure() -> StreamingResponse:
        return StreamingResponse(failing_body(), status_code=201)

    test_app.add_middleware(RequestLoggingMiddleware)
    caplog.set_level(logging.ERROR, logger="taskhub.request")

    with TestClient(test_app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/late-failure")

    assert response.status_code == 201
    records = [
        record
        for record in caplog.records
        if record.name == "taskhub.request" and "/late-failure" in record.message
    ]
    assert len(records) == 1
    assert (
        "HTTP GET /late-failure failed after response start with status 201"
        in records[0].message
    )


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
        record.levelno == logging.ERROR and "status 503" in record.message
        for record in caplog.records
        if record.name == "taskhub.request"
    )
