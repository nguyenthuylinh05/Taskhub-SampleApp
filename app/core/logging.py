"""Application logging configuration."""

import logging
from collections.abc import Callable
from typing import TextIO

from app.core.logging_context import request_id_context


class RequestIdLogRecordFactory:
    """Add the active request ID without changing logging handlers."""

    def __init__(
        self,
        original_factory: Callable[..., logging.LogRecord],
    ) -> None:
        self.original_factory = original_factory

    def __call__(
        self,
        *args: object,
        **kwargs: object,
    ) -> logging.LogRecord:
        record = self.original_factory(*args, **kwargs)
        record.__dict__["request_id"] = request_id_context.get() or "-"
        return record


class _TaskhubStreamHandler(logging.StreamHandler[TextIO]):
    """Handler owned by the Taskhub application logger."""


def _install_request_id_record_factory() -> None:
    factory = logging.getLogRecordFactory()

    if not isinstance(factory, RequestIdLogRecordFactory):
        logging.setLogRecordFactory(RequestIdLogRecordFactory(factory))


def _configure_application_logger(
    logger: logging.Logger,
    level: int,
    formatter: logging.Formatter,
    root_has_handlers: bool,
) -> None:
    logger.setLevel(level)
    logger.disabled = False

    owned_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, _TaskhubStreamHandler)
    ]
    external_handlers = [
        handler
        for handler in logger.handlers
        if not isinstance(handler, _TaskhubStreamHandler)
    ]

    if root_has_handlers or external_handlers:
        for handler in owned_handlers:
            logger.removeHandler(handler)
        if not external_handlers:
            logger.propagate = True
        return

    if owned_handlers:
        handler = owned_handlers[0]
        for duplicate in owned_handlers[1:]:
            logger.removeHandler(duplicate)
    else:
        handler = _TaskhubStreamHandler()
        logger.addHandler(handler)

    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.propagate = False


def configure_logging(log_level: str) -> None:
    """Configure Taskhub loggers while preserving host-owned handlers."""

    level = logging.getLevelName(log_level)

    if not isinstance(level, int):
        raise ValueError(f"Invalid logging level: {log_level}")

    _install_request_id_record_factory()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | request_id=%(request_id)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_logger = logging.getLogger("app")
    taskhub_logger = logging.getLogger("taskhub")

    _configure_application_logger(
        app_logger,
        level,
        formatter,
        bool(root_logger.handlers),
    )
    _configure_application_logger(
        taskhub_logger,
        level,
        formatter,
        bool(root_logger.handlers),
    )

    request_logger = logging.getLogger("taskhub.request")
    request_logger.disabled = False

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(max(uvicorn_logger.level, logging.WARNING))
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(max(uvicorn_error_logger.level, logging.WARNING))
    logging.getLogger("uvicorn.access").disabled = True
