"""Application logging configuration."""

import logging


def configure_logging(log_level: str) -> None:
    """Configure application-wide logging."""

    level = getattr(logging, log_level.upper(), None)

    if not isinstance(level, int):
        raise ValueError(f"Invalid logging level: {log_level}")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt=(
                    "%(asctime)s | %(levelname)s | "
                    "%(name)s | %(message)s"
                ),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(handler)

    request_logger = logging.getLogger("taskhub.request")
    request_logger.setLevel(level)
    request_logger.propagate = True
