from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    CurrentUserDep,
    WorkspaceAccess,
    require_workspace_editor,
    require_workspace_member,
    require_workspace_owner,
)
from app.core.constants import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
)
from app.core.dependencies import WorkspaceServiceDep
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

WorkspaceMemberDep = Annotated[
    WorkspaceAccess,
    Depends(require_workspace_member),
]
WorkspaceEditorDep = Annotated[
    WorkspaceAccess,
    Depends(require_workspace_editor),
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
    return await service.create_workspace(data, current_user)


@router.get("", response_model=WorkspaceListResponse)
async def get_workspaces(
    current_user: CurrentUserDep,
    service: WorkspaceServiceDep,
    page: Annotated[int, Query(ge=1)] = DEFAULT_PAGE,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> WorkspaceListResponse:
    return await service.get_workspaces(current_user, page, limit)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    access: WorkspaceMemberDep,
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(access.workspace)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
async def update_workspace(
    data: WorkspaceUpdate,
    access: WorkspaceEditorDep,
    service: WorkspaceServiceDep,
) -> WorkspaceResponse:
    return await service.update_workspace(access.workspace, data)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace(
    access: WorkspaceOwnerDep,
    service: WorkspaceServiceDep,
) -> None:
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
    await service.remove_member(access.workspace, user_id)
