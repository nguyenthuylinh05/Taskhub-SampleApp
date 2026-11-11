from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    WorkspaceAccess,
    require_workspace_editor,
    require_workspace_member,
)
from app.core.dependencies import ProjectServiceDep
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
)

WorkspaceMemberDep = Annotated[
    WorkspaceAccess,
    Depends(require_workspace_member),
]

WorkspaceEditorDep = Annotated[
    WorkspaceAccess,
    Depends(require_workspace_editor),
]


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    workspace_id: int,
    data: ProjectCreate,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> ProjectResponse:
    return await service.create_project(access.workspace.id, data)


@router.get("", response_model=list[ProjectResponse])
async def get_projects(
    workspace_id: int,
    service: ProjectServiceDep,
    access: WorkspaceMemberDep,
) -> list[ProjectResponse]:
    return await service.get_projects(access.workspace.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    workspace_id: int,
    project_id: int,
    service: ProjectServiceDep,
    access: WorkspaceMemberDep,
) -> ProjectResponse:
    return await service.get_project(access.workspace.id, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    workspace_id: int,
    project_id: int,
    data: ProjectUpdate,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> ProjectResponse:
    return await service.update_project(
        access.workspace.id,
        project_id,
        data,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    workspace_id: int,
    project_id: int,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> Response:
    await service.delete_project(access.workspace.id, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
