"""Shared OpenAPI response documentation for API routers."""

from typing import Any

ApiResponses = dict[int | str, dict[str, Any]]

PROTECTED_API_RESPONSES: ApiResponses = {
    401: {"description": "Missing, invalid, or expired access token"},
    403: {"description": "Authenticated user lacks permission for this operation"},
    404: {"description": "Requested resource was not found or is inaccessible"},
    500: {"description": "Unexpected server error"},
}

PUBLIC_API_RESPONSES: ApiResponses = {
    500: {"description": "Unexpected server error"},
}
