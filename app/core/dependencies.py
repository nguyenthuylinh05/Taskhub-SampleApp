from typing import Annotated, cast

from fastapi import Depends, Request

from app.repositories.project import InMemoryProjectRepository
from app.services.project import ProjectService


def get_project_repository(
    request: Request,
) -> InMemoryProjectRepository:
    """Get project repository from application state."""

    return cast(
        InMemoryProjectRepository,
        request.app.state.project_repository,
    )


ProjectRepositoryDep = Annotated[
    InMemoryProjectRepository,
    Depends(get_project_repository),
]


def get_project_service(
    repository: ProjectRepositoryDep,
) -> ProjectService:
    """Create project service with injected repository."""

    return ProjectService(repository)


ProjectServiceDep = Annotated[
    ProjectService,
    Depends(get_project_service),
]
