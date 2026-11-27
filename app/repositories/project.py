from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectResponse


class InMemoryProjectRepository:
    """Temporary in-memory repository for Day 1."""

    def __init__(self) -> None:
        self._projects: dict[UUID, ProjectResponse] = {}

    async def create(
        self,
        project: ProjectResponse,
    ) -> ProjectResponse:
        self._projects[project.id] = project
        return project

    async def get_by_id(
        self,
        project_id: UUID,
    ) -> ProjectResponse | None:
        return self._projects.get(project_id)

    async def get_all(self) -> list[ProjectResponse]:
        return list(self._projects.values())

    async def update(
        self,
        project: ProjectResponse,
    ) -> ProjectResponse | None:
        if project.id not in self._projects:
            return None

        self._projects[project.id] = project
        return project

    async def delete(self, project_id: UUID) -> bool:
        if project_id not in self._projects:
            return False

        del self._projects[project_id]
        return True


class ProjectRepository(BaseRepository[Project]):
    """Repository for project database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project)
