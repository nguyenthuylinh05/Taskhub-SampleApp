from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentUserDep,
    WorkspaceAccess,
    require_workspace_member,
    require_workspace_owner,
)
from app.api.openapi import PROTECTED_API_RESPONSES
from app.core.dependencies import PaginationDep, WorkspaceServiceDep
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
    responses=PROTECTED_API_RESPONSES,
)

WorkspaceMemberDep = Annotated[
    WorkspaceAccess,
    Depends(require_workspace_member),
]
WorkspaceOwnerDep = Annotated[
    WorkspaceAccess,
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
    """Create a workspace owned by the authenticated user."""
    return await service.create_workspace(data, current_user)


@router.get("", response_model=WorkspaceListResponse)
async def get_workspaces(
    current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
    pagination: PaginationDep,
) -> WorkspaceListResponse:
    """List accessible workspaces with pagination."""
    return await service.get_workspaces(current_user, pagination)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    access: WorkspaceMemberDep,
) -> WorkspaceResponse:
    """Get a workspace visible to the authenticated user."""
    return WorkspaceResponse.model_validate(access.workspace)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
async def update_workspace(
    data: WorkspaceUpdate,
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    """Update workspace details. Requires OWNER access."""
    return await service.update_workspace(access.workspace, data)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> None:
    """Delete a workspace and its dependent resources. Requires OWNER access."""
    await service.delete_workspace(access.workspace)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    data: WorkspaceMemberAdd,
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> WorkspaceMemberResponse:
    """Add an existing user with a workspace role. Requires OWNER access."""
    return await service.add_member(
        access.workspace,
        data.user_id,
        data.role,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
)
async def get_workspace_members(
    access: WorkspaceMemberDep,
    service: WorkspaceServiceDep,
) -> list[WorkspaceMemberResponse]:
    """List workspace members and their roles."""
    return await service.get_workspace_members(access.workspace)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workspace_member(
    user_id: int,
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> None:
    """Remove a workspace member. Requires OWNER access."""
    await service.remove_member(access.workspace, user_id)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    summary="Change a workspace member's role",
    description=(
        "Change an existing workspace member's role between EDITOR and VIEWER. "
        "Requires OWNER access."
    ),
    responses={
        400: {"description": "Role change violates workspace rules"},
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Workspace or member not found"},
    },
)
async def change_workspace_member_role(
    user_id: int,
    data: WorkspaceMemberRoleUpdate,
    current_user: CurrentUserDep,
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> WorkspaceMemberResponse:
    """Change a workspace member's role. Requires OWNER access."""
    return await service.change_member_role(
        access.workspace,
        current_user,
        user_id,
        data.role,
    )
