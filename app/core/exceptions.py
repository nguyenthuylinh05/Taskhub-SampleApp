"""Custom application exceptions."""

from fastapi import status

from app.core import messages


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
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

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(message, status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    """Raised when application-level validation fails."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_CONTENT)


class EmailAlreadyRegistered(AppException):
    """Raised when an email is already registered."""

    def __init__(self) -> None:
        super().__init__(
            message=messages.EMAIL_ALREADY_REGISTERED,
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidCredentials(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InactiveUser(AppException):
    """Raised when a user account is inactive."""

    def __init__(self) -> None:
        super().__init__(
            message=messages.USER_INACTIVE,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidRefreshToken(AppException):
    """Raised when a refresh token is invalid or revoked."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid or revoked refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PermissionDenied(AppException):
    """Raised when a user lacks permission to perform an action."""

    def __init__(self) -> None:
        super().__init__(
            message="You do not have permission to perform this action",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidOperation(AppException):
    """Raised when an operation violates business rules."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class CannotDeleteOwnAccount(AppException):
    """Raised when a user attempts to delete their own account."""

    def __init__(self) -> None:
        super().__init__(
            message=messages.CANNOT_DELETE_OWN_ACCOUNT,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidCurrentPassword(AppException):
    """Raised when the current password is incorrect."""

    def __init__(
        self,
        message: str = "Current password is incorrect",
    ) -> None:
        super().__init__(message, status.HTTP_400_BAD_REQUEST)
