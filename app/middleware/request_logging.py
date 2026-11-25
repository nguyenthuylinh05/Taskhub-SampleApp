"""HTTP request logging middleware."""

import asyncio
import logging
import re
from contextvars import Token
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging_context import request_id_context

logger = logging.getLogger("taskhub.request")

REQUEST_ID_HEADER = b"x-request-id"
REQUEST_ID_PATTERN = re.compile(rb"[A-Za-z0-9._-]{1,64}")


class RequestLoggingMiddleware:
    """Log HTTP requests using the pure ASGI middleware interface."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = perf_counter()
        request_id = self._get_request_id(scope)

        scope.setdefault("state", {})["request_id"] = request_id
        context_token: Token[str | None] = request_id_context.set(request_id)
        status_code: int | None = None
        response_started = False
        failed = False
        cancelled = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code

            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True

        try:
            await self.app(scope, receive, send_with_request_id)
        except asyncio.CancelledError:
            cancelled = True
            raise
        except Exception:
            failed = True
            raise
        finally:
            try:
                duration_ms = (perf_counter() - start_time) * 1000

                if cancelled:
                    log_level = logging.WARNING
                    outcome = "cancelled"
                    status_label: int | str = (
                        status_code if status_code is not None else "not started"
                    )
                elif failed:
                    log_level = logging.ERROR
                    outcome = (
                        "failed after response start" if response_started else "failed"
                    )
                    status_label = status_code if status_code is not None else 500
                else:
                    outcome = "completed"
                    final_status = status_code if status_code is not None else 500
                    status_label = final_status
                    if 500 <= final_status <= 599:
                        log_level = logging.ERROR
                    elif 400 <= final_status <= 499:
                        log_level = logging.WARNING
                    else:
                        log_level = logging.INFO

                logger.log(
                    log_level,
                    "HTTP %s %s %s with status %s in %.2f ms request_id=%s",
                    scope["method"],
                    scope["path"],
                    outcome,
                    status_label,
                    duration_ms,
                    request_id,
                )
            finally:
                request_id_context.reset(context_token)

    @staticmethod
    def _get_request_id(scope: Scope) -> str:
        """Get a safe request ID or generate a new one."""

        incoming_ids = [
            value
            for name, value in scope.get("headers", [])
            if name.lower() == REQUEST_ID_HEADER
        ]

        if len(incoming_ids) == 1 and REQUEST_ID_PATTERN.fullmatch(incoming_ids[0]):
            decoded_id: str = incoming_ids[0].decode("ascii")
            return decoded_id

        return uuid4().hex
