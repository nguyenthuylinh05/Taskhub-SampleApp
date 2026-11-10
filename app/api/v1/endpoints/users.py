from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_current_user, require_admin
from app.core import messages
from app.core.dependencies import AuthServiceDep, UserRepositoryDep
from app.core.exceptions import (
    AppException,
    EmailAlreadyRegistered,
    NotFoundException,
)
from app.core.security import hash_password
from app.models import User, UserRole
from app.schemas.user import (
    ChangePasswordRequest,
    UserCreate,
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_current_user_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: AuthServiceDep,
) -> Response:
    await auth_service.change_password(current_user, data)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    repository: UserRepositoryDep,
) -> UserResponse:
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise AppException(
            messages.UPDATE_FIELDS_REQUIRED,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if any(value is None for value in update_data.values()):
        raise AppException(
            messages.UPDATE_FIELDS_CANNOT_BE_NULL,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if "email" in update_data:
        existing_user = await repository.get_by_email(update_data["email"])

        if existing_user is not None and existing_user.id != current_user.id:
            raise EmailAlreadyRegistered()

    try:
        user = await repository.update(current_user.id, update_data)
    except IntegrityError as exc:
        await repository.session.rollback()
        raise EmailAlreadyRegistered() from exc

    if user is None:
        raise NotFoundException(messages.USER_NOT_FOUND)

    return UserResponse.model_validate(user)


@router.get("/", dependencies=[Depends(require_admin)])
async def get_users(
    repository: UserRepositoryDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, object]:
    users, total = await repository.get_paginated(
        page=page,
        limit=limit,
    )

    return {
        "items": [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at,
            }
            for user in users
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{user_id}", dependencies=[Depends(require_admin)])
async def get_user(
    user_id: int,
    repository: UserRepositoryDep,
) -> dict[str, object]:
    user = await repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(
    user_data: UserCreate,
    repository: UserRepositoryDep,
) -> UserResponse:
    existing_user = await repository.get_by_email(
        user_data.email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_data_dict = user_data.model_dump(exclude={"password"})
    user_data_dict["hashed_password"] = await run_in_threadpool(
        hash_password,
        user_data.password,
    )

    user = await repository.create(user_data_dict)

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    repository: UserRepositoryDep,
) -> UserResponse:
    update_data = user_data.model_dump(exclude_unset=True)

    if any(value is None for value in update_data.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Update fields cannot be null",
        )

    target_user = await repository.get_by_id(user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if "email" in update_data:
        existing_user = await repository.get_by_email(update_data["email"])
        if existing_user is not None and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Prevent removing the last active admin.
    removes_admin_access = (
        target_user.role == UserRole.ADMIN
        and target_user.is_active
        and (
            update_data.get("role") == UserRole.MEMBER
            or update_data.get("is_active") is False
        )
    )

    if removes_admin_access and await repository.count_active_admins() <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove or deactivate the last active admin",
        )

    user = await repository.update(user_id, update_data)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: int,
    repository: UserRepositoryDep,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    # Prevent an admin from deleting their own account.
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete your own account",
        )

    target_user = await repository.get_by_id(user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent deleting the last active admin.
    if (
        target_user.role == UserRole.ADMIN
        and target_user.is_active
        and await repository.count_active_admins() <= 1
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete the last active admin",
        )

    deleted = await repository.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
