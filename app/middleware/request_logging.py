"""HTTP request logging middleware."""

import logging
import re
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

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

        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append(
                    (REQUEST_ID_HEADER, request_id.encode("ascii"))
                )

                message = {
                    **message,
                    "headers": headers,
                }

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            duration_ms = (perf_counter() - start_time) * 1000

            logger.error(
                (
                    "HTTP %s %s failed with status 500 "
                    "in %.2f ms request_id=%s"
                ),
                scope["method"],
                scope["path"],
                duration_ms,
                request_id,
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1000

        if 500 <= status_code <= 599:
            log_level = logging.ERROR
        elif 400 <= status_code <= 499:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        logger.log(
            log_level,
        (
        "HTTP %s %s completed with status %s "
        "in %.2f ms request_id=%s"
        ),
        scope["method"],
        scope["path"],
        status_code,
        duration_ms,
        request_id,
    )

    @staticmethod
    def _get_request_id(scope: Scope) -> str:
        """Get a safe request ID or generate a new one."""

        headers = {
            name: value
            for name, value in scope.get("headers", [])
        }
        incoming_id: bytes | None = headers.get(REQUEST_ID_HEADER)

        if (
            incoming_id is not None
            and REQUEST_ID_PATTERN.fullmatch(incoming_id)
        ):
            decoded_id: str = incoming_id.decode("ascii")
            return decoded_id

        return uuid4().hex
