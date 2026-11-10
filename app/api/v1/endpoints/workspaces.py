from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    get_current_user,
    require_workspace_editor,
    require_workspace_member,
    require_workspace_owner,
)
from app.core.dependencies import (
    UserRepositoryDep,
    WorkspaceRepositoryDep,
    WorkspaceServiceDep,
)
from app.core.exceptions import ResourceNotFound
from app.models import User, WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
WorkspaceMemberDep = Annotated[
    WorkspaceRole,
    Depends(require_workspace_member),
]
WorkspaceEditorDep = Annotated[
    WorkspaceRole,
    Depends(require_workspace_editor),
]
WorkspaceOwnerDep = Annotated[
    WorkspaceRole,
    Depends(require_workspace_owner),
]


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """Create a workspace."""

    return await service.create_workspace(data, current_user)


@router.get(
    "",
    response_model=list[WorkspaceResponse],
)
async def get_workspaces(
    current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
) -> list[WorkspaceResponse]:
    """Get workspaces owned or joined by current user."""

    return await service.get_workspaces(current_user)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
async def get_workspace(
    workspace_id: int,
    _: WorkspaceMemberDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """Get workspace details."""

    return await service.get_workspace(workspace_id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    _: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """Update workspace. Only owner or admin."""

    return await service.update_workspace(workspace_id, data)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    workspace_id: int,
    _: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> None:
    """Delete workspace. Only owner or admin."""

    await service.delete_workspace(workspace_id)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: int,
    data: WorkspaceMemberAdd,
    _: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> WorkspaceMemberResponse:
    """Add a member. Only owner or admin."""

    return await service.add_member(
        workspace_id,
        data.user_id,
        data.role,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
)
async def get_workspace_members(
    workspace_id: int,
    _: WorkspaceMemberDep,
    workspace_repository: WorkspaceRepositoryDep,
    user_repository: UserRepositoryDep,
) -> list[WorkspaceMemberResponse]:
    """Get workspace members, including the owner."""

    workspace = await workspace_repository.get_by_id(workspace_id)

    if workspace is None:
        raise ResourceNotFound()

    members = await workspace_repository.get_workspace_members(workspace_id)

    responses = [
        WorkspaceMemberResponse(user_id=user.id, role=role)
        for user, role in members
    ]

    owner = await user_repository.get_by_id(workspace.owner_id)

    if owner is not None:
        responses.insert(
            0,
            WorkspaceMemberResponse(
                user_id=owner.id,
                role=WorkspaceRole.OWNER,
            ),
        )

    return responses


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workspace_member(
    workspace_id: int,
    user_id: int,
    _: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> None:
    """Remove a member. Only owner or admin."""

    await service.remove_member(workspace_id, user_id)
