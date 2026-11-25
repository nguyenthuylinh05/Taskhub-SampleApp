"""Tests for logging configuration."""

import io
import logging

import pytest
from app.core.config import Settings
from app.core.logging import RequestIdLogRecordFactory, configure_logging
from app.core.logging_context import request_id_context


def test_log_level_is_normalized_before_literal_validation() -> None:
    """Lowercase LOG_LEVEL values are normalized to the supported Literal."""

    settings = Settings(
        _env_file=None,
        DEBUG=False,
        LOG_LEVEL="info",
        POSTGRES_PASSWORD="test-postgres-password",
        JWT_SECRET_KEY="test-jwt-secret-key-with-more-than-32-chars",
    )

    assert settings.LOG_LEVEL == "INFO"


@pytest.mark.parametrize(
    ("log_level", "expected_level"),
    [
        ("INFO", logging.INFO),
        ("DEBUG", logging.DEBUG),
    ],
)
def test_app_namespace_uses_configured_level_and_request_id(
    log_level: str,
    expected_level: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Application namespace logs honor LOG_LEVEL and include request IDs."""

    configure_logging(log_level)
    logger = logging.getLogger("app.services.example")
    app_logger = logging.getLogger("app")
    root_logger = logging.getLogger()
    root_handler_count = len(root_logger.handlers)

    configure_logging(log_level)

    assert len(root_logger.handlers) == root_handler_count
    assert root_logger.level == logging.WARNING
    assert app_logger.level == expected_level
    assert app_logger.disabled is False
    assert app_logger.propagate is True
    assert logger.getEffectiveLevel() == expected_level

    caplog.handler.setLevel(logging.DEBUG)
    token = request_id_context.set("app-namespace-trace")
    try:
        logger.log(expected_level, "application event")
    finally:
        request_id_context.reset(token)

    record = next(
        record for record in caplog.records if record.name == "app.services.example"
    )
    assert record.levelno == expected_level
    assert record.__dict__["request_id"] == "app-namespace-trace"


def test_configure_logging_preserves_external_root_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """External root handler formatting and filters remain unchanged."""

    root_logger = logging.getLogger()
    handler = logging.StreamHandler(io.StringIO())
    formatter = logging.Formatter("external %(message)s")
    handler_filter = logging.Filter("external")
    handler.setFormatter(formatter)
    handler.addFilter(handler_filter)
    original_level = root_logger.level
    root_logger.addHandler(handler)

    try:
        configure_logging("INFO")
        configure_logging("INFO")

        assert handler.formatter is formatter
        assert handler.filters == [handler_filter]
        assert root_logger.handlers.count(handler) == 1
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(original_level)


def test_repeated_configure_does_not_wrap_record_factory_again() -> None:
    """Repeated setup reuses the request-ID record factory wrapper."""

    configure_logging("INFO")
    factory = logging.getLogRecordFactory()
    configure_logging("DEBUG")
    configure_logging("INFO")

    assert logging.getLogRecordFactory() is factory
    assert isinstance(factory, RequestIdLogRecordFactory)
    assert not isinstance(factory.original_factory, RequestIdLogRecordFactory)


def test_configure_logging_disables_uvicorn_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Access logs are disabled while Uvicorn operational errors remain enabled."""

    access_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger = logging.getLogger("uvicorn")
    error_logger = logging.getLogger("uvicorn.error")
    monkeypatch.setattr(access_logger, "disabled", False)
    monkeypatch.setattr(uvicorn_logger, "level", uvicorn_logger.level)
    monkeypatch.setattr(error_logger, "level", logging.INFO)
    monkeypatch.setattr(error_logger, "disabled", False)

    configure_logging("INFO")

    assert access_logger.disabled is True
    assert error_logger.level == logging.WARNING
    assert error_logger.disabled is False


def test_host_root_handler_controls_propagated_third_party_debug_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A permissive host handler accepts DEBUG propagated past root WARNING."""

    root_logger = logging.getLogger()
    app_logger = logging.getLogger("app")
    app_service_logger = logging.getLogger("app.services.example")
    third_party_logger = logging.getLogger("review.thirdparty.explicit_debug")
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    formatter = logging.Formatter(
        "%(name)s %(levelname)s request_id=%(request_id)s %(message)s"
    )
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)

    for logger in (
        app_logger,
        app_service_logger,
        third_party_logger,
    ):
        monkeypatch.setattr(logger, "handlers", [])
        monkeypatch.setattr(logger, "level", logging.NOTSET)
        monkeypatch.setattr(logger, "disabled", False)
        monkeypatch.setattr(logger, "propagate", True)

    monkeypatch.setattr(root_logger, "handlers", [handler])
    monkeypatch.setattr(root_logger, "level", logging.NOTSET)

    configure_logging("INFO")
    third_party_logger.setLevel(logging.DEBUG)
    app_service_logger.setLevel(logging.NOTSET)

    request_token = request_id_context.set("app-info-trace")
    try:
        third_party_logger.debug("third-party debug reaches host handler")
        app_service_logger.debug("application debug follows LOG_LEVEL")
        app_service_logger.info("application info reaches host handler")
    finally:
        request_id_context.reset(request_token)

    assert root_logger.level == logging.WARNING
    assert root_logger.handlers == [handler]
    assert handler.level == logging.NOTSET
    assert handler.formatter is formatter
    assert "third-party debug reaches host handler" in output.getvalue()
    assert "application debug follows LOG_LEVEL" not in output.getvalue()
    assert "application info reaches host handler" in output.getvalue()
    assert output.getvalue().count("request_id=app-info-trace") == 2
