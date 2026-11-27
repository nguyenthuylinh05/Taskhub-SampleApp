from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    WorkspaceAccess,
    require_workspace_editor,
    require_workspace_member,
)
from app.api.openapi import PROTECTED_API_RESPONSES
from app.core.dependencies import ProjectServiceDep
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
    responses=PROTECTED_API_RESPONSES,
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
    summary="Create a project",
    responses={
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Workspace not found"},
    },
)
async def create_project(
    workspace_id: int,
    data: ProjectCreate,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> ProjectResponse:
    """Create a project in the workspace. Requires OWNER or EDITOR access."""
    return await service.create_project(access.workspace.id, data)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List projects in a workspace",
    responses={
        404: {"description": "Workspace not found"},
    },
)
async def get_projects(
    workspace_id: int,
    service: ProjectServiceDep,
    access: WorkspaceMemberDep,
) -> list[ProjectResponse]:
    """List projects in the accessible workspace."""
    return await service.get_projects(access.workspace.id)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project",
    responses={
        404: {"description": "Project or workspace not found"},
    },
)
async def get_project(
    workspace_id: int,
    project_id: int,
    service: ProjectServiceDep,
    access: WorkspaceMemberDep,
) -> ProjectResponse:
    """Get project details within the accessible workspace."""
    return await service.get_project(access.workspace.id, project_id)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    responses={
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Project or workspace not found"},
    },
)
async def update_project(
    workspace_id: int,
    project_id: int,
    data: ProjectUpdate,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> ProjectResponse:
    """Update a project, including its ACTIVE or ARCHIVED status."""
    return await service.update_project(
        access.workspace.id,
        project_id,
        data,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses={
        403: {"description": "Insufficient workspace permissions"},
        404: {"description": "Project or workspace not found"},
    },
)
async def delete_project(
    workspace_id: int,
    project_id: int,
    service: ProjectServiceDep,
    access: WorkspaceEditorDep,
) -> Response:
    """Delete a project in the workspace. Requires OWNER or EDITOR access."""
    await service.delete_project(access.workspace.id, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
