from fastapi import APIRouter, HTTPException, Query, Response, status

from app.core.dependencies import UserRepositoryDep
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/")
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


@router.get("/{user_id}")
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
    user_data_dict["hashed_password"] = hash_password(
        user_data.password,
    )

    user = await repository.create(user_data_dict)

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
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

    if "email" in update_data:
        existing_user = await repository.get_by_email(update_data["email"])
        if existing_user is not None and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
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
)
async def delete_user(
    user_id: int,
    repository: UserRepositoryDep,
) -> Response:
    deleted = await repository.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
