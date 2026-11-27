from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.repositories.project import InMemoryProjectRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)


class ProjectService:
    """Business logic for project operations."""

    def __init__(
        self,
        repository: InMemoryProjectRepository,
    ) -> None:
        self.repository = repository

    async def create_project(
        self,
        data: ProjectCreate,
    ) -> ProjectResponse:
        project = ProjectResponse(
            id=uuid4(),
            name=data.name,
            description=data.description,
            created_at=datetime.now(UTC),
        )

        return await self.repository.create(project)

    async def get_projects(self) -> list[ProjectResponse]:
        return await self.repository.get_all()

    async def get_project(
        self,
        project_id: UUID,
    ) -> ProjectResponse | None:
        return await self.repository.get_by_id(project_id)

    async def update_project(
        self,
        project_id: UUID,
        data: ProjectUpdate,
    ) -> ProjectResponse | None:
        existing = await self.repository.get_by_id(project_id)

        if existing is None:
            return None

        updated = existing.model_copy(update=data.model_dump(exclude_unset=True))

        return await self.repository.update(updated)

    async def delete_project(self, project_id: UUID) -> bool:
        return await self.repository.delete(project_id)
