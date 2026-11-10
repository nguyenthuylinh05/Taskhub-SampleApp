from fastapi import status


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


class EmailAlreadyRegistered(AppException):
    """Raised when an email is already registered."""

    def __init__(self) -> None:
        super().__init__(
            message="Email is already registered",
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
            message="Inactive user",
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
    """Raised when a user does not have permission to perform an action."""

    def __init__(self) -> None:
        super().__init__(
            message="You do not have permission to perform this action",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFound(AppException):
    """Raised when a resource does not exist or is not accessible."""

    def __init__(self) -> None:
        super().__init__(
            message="Resource not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(AppException):
    """Raised when a resource conflicts with the current state."""

    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class InvalidOperation(AppException):
    """Raised when an operation violates business rules."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )