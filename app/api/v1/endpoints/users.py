"""User API endpoints."""

from fastapi import APIRouter, Query, Response, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser
from app.core.dependencies import AuthServiceDep, UserRepositoryDep, UserServiceDep
from app.core.exceptions import (
    EmailAlreadyRegistered,
    NotFoundException,
    ValidationException,
)
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
)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_current_user_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> Response:
    """Change the password of the currently authenticated user."""
    await auth_service.change_password(current_user, data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserProfileUpdate,
    current_user: CurrentUser,
    repository: UserRepositoryDep,
) -> UserResponse:
    """Update the profile of the currently authenticated user."""
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise ValidationException("At least one field must be provided")

    if any(value is None for value in update_data.values()):
        raise ValidationException("Update fields cannot be null")

    if "email" in update_data:
        update_data["email"] = str(update_data["email"])

        existing_user = await repository.get_by_email(update_data["email"])

        if existing_user is not None and existing_user.id != current_user.id:
            raise EmailAlreadyRegistered()

    try:
        user = await repository.update(current_user.id, update_data)

        if user is None:
            raise NotFoundException("User not found")

        await repository.session.commit()

    except IntegrityError as exc:
        await repository.session.rollback()
        raise EmailAlreadyRegistered() from exc

    except Exception:
        await repository.session.rollback()
        raise

    return UserResponse.model_validate(user)


@router.get("/", response_model=UserListResponse)
async def get_users(
    service: UserServiceDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> UserListResponse:
    """Get a paginated list of users."""
    users, total = await service.get_users(
        page=page,
        limit=limit,
    )

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserServiceDep,
) -> UserResponse:
    """Get a user by ID."""
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    service: UserServiceDep,
) -> UserResponse:
    """Create a new user."""
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserServiceDep,
) -> UserResponse:
    """Update an existing user."""
    user = await service.update_user(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    service: UserServiceDep,
) -> Response:
    """Delete a user."""
    await service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
