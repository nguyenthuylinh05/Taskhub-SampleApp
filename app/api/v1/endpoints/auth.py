from fastapi import APIRouter, status

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
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
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
)
async def login(
    data: LoginRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""

    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    service: AuthServiceDep,
) -> TokenResponse:
    """Rotate refresh token and issue new tokens."""

    return await service.refresh(data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    service: AuthServiceDep,
) -> None:
    """Revoke a refresh token."""

    await service.logout(data)
