from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import CurrentUserDep, require_admin
from app.api.openapi import PROTECTED_API_RESPONSES
from app.core.dependencies import AuthServiceDep, PaginationDep, UserServiceDep
from app.schemas.user import (
    ChangePasswordRequest,
    UserCreate,
    UserListResponse,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses=PROTECTED_API_RESPONSES,
)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUserDep,
) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user's password",
)
async def change_current_user_password(
    data: ChangePasswordRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> Response:
    """Change the current user's password and revoke refresh sessions."""
    await auth_service.change_password(current_user, data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserProfileUpdate,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserResponse:
    """Update the authenticated user's profile fields."""
    return await user_service.update_profile(
        current_user.id,
        user_data,
    )


@router.get(
    "/",
    dependencies=[Depends(require_admin)],
    response_model=UserListResponse,
    summary="List users",
)
async def get_users(
    user_service: UserServiceDep,
    pagination: PaginationDep,
) -> UserListResponse:
    """List users with pagination. Requires the system ADMIN role."""
    return await user_service.get_users(
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{user_id}",
    dependencies=[Depends(require_admin)],
    response_model=UserResponse,
    summary="Get a user by ID",
    responses={
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    user_service: UserServiceDep,
) -> UserResponse:
    """Get one user by ID. Requires the system ADMIN role."""
    return await user_service.get_user(user_id)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Create a user",
    responses={
        409: {"description": "Email is already registered"},
    },
)
async def create_user(
    user_data: UserCreate,
    user_service: UserServiceDep,
) -> UserResponse:
    """Create a user account. Requires the system ADMIN role."""
    return await user_service.create_user(user_data)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
    summary="Update a user",
    responses={
        404: {"description": "User not found"},
        409: {"description": "Email is already registered or update conflicts"},
    },
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserServiceDep,
) -> UserResponse:
    """Update a user account. Requires the system ADMIN role."""
    return await user_service.update_user(
        user_id,
        user_data,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
    summary="Delete a user",
    responses={
        404: {"description": "User not found"},
        409: {"description": "User cannot be deleted"},
    },
)
async def delete_user(
    user_id: int,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> Response:
    """Delete a user account. Requires the system ADMIN role."""
    await user_service.delete_user(
        user_id,
        requester_id=current_user.id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
