from app.core.exceptions import NotFoundException
from app.core.messages import PROJECT_NOT_FOUND
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


class ProjectService:
    """Business logic for workspace projects."""

    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    async def create_project(
        self,
        workspace_id: int,
        data: ProjectCreate,
    ) -> ProjectResponse:
        project = await self.repository.create(
            {
                "workspace_id": workspace_id,
                "name": data.name,
                "description": data.description,
            }
        )
        return ProjectResponse.model_validate(project)

    async def get_projects(
        self,
        workspace_id: int,
    ) -> list[ProjectResponse]:
        projects = await self.repository.get_by_workspace_id(workspace_id)
        return [
            ProjectResponse.model_validate(project)
            for project in projects
        ]

    async def get_project(
        self,
        workspace_id: int,
        project_id: int,
    ) -> ProjectResponse:
        project = await self.repository.get_in_workspace(
            project_id,
            workspace_id,
        )
        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)

        return ProjectResponse.model_validate(project)

    async def update_project(
        self,
        workspace_id: int,
        project_id: int,
        data: ProjectUpdate,
    ) -> ProjectResponse:
        project = await self.repository.update_in_workspace(
            project_id,
            workspace_id,
            data.model_dump(exclude_unset=True),
        )
        if project is None:
            raise NotFoundException(PROJECT_NOT_FOUND)

        return ProjectResponse.model_validate(project)

    async def delete_project(
        self,
        workspace_id: int,
        project_id: int,
    ) -> None:
        deleted = await self.repository.delete_in_workspace(
            project_id,
            workspace_id,
        )
        if not deleted:
            raise NotFoundException(PROJECT_NOT_FOUND)
