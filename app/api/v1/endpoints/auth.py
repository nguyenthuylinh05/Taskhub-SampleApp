from fastapi import APIRouter, status

from app.api.openapi import PUBLIC_API_RESPONSES
from app.core.dependencies import AuthServiceDep
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses=PUBLIC_API_RESPONSES,
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user account",
    description="Create an account using an email address, name, and password.",
    responses={409: {"description": "Email address is already registered"}},
)
async def register(
    data: RegisterRequest,
    service: AuthServiceDep,
) -> UserResponse:
    """Register a new user."""

    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Validate credentials and issue an access token and refresh token.",
    responses={401: {"description": "Email or password is invalid"}},
)
async def login(
    data: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""

    return await service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh authentication tokens",
    description="Rotate a valid refresh token and issue a new token pair.",
    responses={401: {"description": "Refresh token is invalid or revoked"}},
)
async def refresh(
    data: RefreshRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Rotate refresh token and issue new tokens."""

    return await service.refresh(data)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    description="Revoke the supplied refresh token.",
    responses={401: {"description": "Refresh token is invalid or already revoked"}},
)
async def logout(
    data: RefreshRequest,
    service: AuthServiceDep,
) -> None:
    """Revoke a refresh token."""

    await service.logout(data)
