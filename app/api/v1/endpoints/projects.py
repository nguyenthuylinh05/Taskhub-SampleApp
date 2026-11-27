from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import ProjectServiceDep
from app.core.exceptions import NotFoundException
from app.core.messages import PROJECT_NOT_FOUND
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    data: ProjectCreate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    return await service.create_project(data)


@router.get(
    "",
    response_model=list[ProjectResponse],
)
async def get_projects(
    service: ProjectServiceDep,
) -> list[ProjectResponse]:
    return await service.get_projects()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found",
        },
    },
)
async def get_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.get_project(project_id)

    if project is None:
        raise NotFoundException(PROJECT_NOT_FOUND)

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found",
        },
    },
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.update_project(project_id, data)

    if project is None:
        raise NotFoundException(PROJECT_NOT_FOUND)

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Project not found",
        },
    },
)
async def delete_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> None:
    deleted = await service.delete_project(project_id)

    if not deleted:
        raise NotFoundException(PROJECT_NOT_FOUND)
