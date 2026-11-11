from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for project database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project)

    async def get_by_workspace_id(
        self,
        workspace_id: int,
    ) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.id)
        )
        result = await self.session.scalars(statement)
        return list(result.all())

    async def get_in_workspace(
        self,
        project_id: int,
        workspace_id: int,
    ) -> Project | None:
        statement = select(Project).where(
            Project.id == project_id,
            Project.workspace_id == workspace_id,
        )
        return await self.session.scalar(statement)

    async def update_in_workspace(
        self,
        project_id: int,
        workspace_id: int,
        data: dict,
    ) -> Project | None:
        project = await self.get_in_workspace(project_id, workspace_id)

        if project is None:
            return None

        for key, value in data.items():
            if hasattr(project, key):
                setattr(project, key, value)

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete_in_workspace(
        self,
        project_id: int,
        workspace_id: int,
    ) -> bool:
        statement = delete(Project).where(
            Project.id == project_id,
            Project.workspace_id == workspace_id,
        )
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount > 0
