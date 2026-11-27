"""Context shared by request logging and application log handlers."""

from contextvars import ContextVar

request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)
