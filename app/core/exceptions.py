"""Custom application exceptions."""

from fastapi import status

from app.core import messages


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(AppException):
    """Raised when a resource conflicts with existing data."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    """Raised when application-level validation fails."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_CONTENT)


class EmailAlreadyRegistered(AppException):
    """Raised when a registration email already exists."""

    def __init__(self, message: str = "Email is already registered") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class InvalidCredentials(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class InactiveUser(AppException):
    """Raised when an inactive user attempts an authenticated action."""

    def __init__(self, message: str = messages.USER_INACTIVE) -> None:
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class InvalidRefreshToken(AppException):
    """Raised when a refresh token is invalid or revoked."""

    def __init__(
        self,
        message: str = "Invalid or expired refresh token",
    ) -> None:
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class InvalidCurrentPassword(AppException):
    """Raised when the current password is incorrect."""

    def __init__(
        self,
        message: str = "Current password is incorrect",
    ) -> None:
        super().__init__(message, status.HTTP_400_BAD_REQUEST)
