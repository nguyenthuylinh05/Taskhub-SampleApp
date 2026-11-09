from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_project_service
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project import ProjectService

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

ProjectServiceDep = Annotated[
    ProjectService,
    Depends(get_project_service),
]


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
)
async def get_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.get_project(project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    project = await service.update_project(project_id, data)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> None:
    deleted = await service.delete_project(project_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
