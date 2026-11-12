from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.messages import WORKSPACE_MEMBER_ALREADY_EXISTS
from app.models import User, Workspace, WorkspaceRole
from app.models.workspace import workspace_members
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository for workspace database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workspace)

    async def get_user_workspaces_paginated(
        self,
        user_id: int,
        page: int,
        limit: int,
    ) -> tuple[list[Workspace], int]:
        """Get owned or joined workspaces with pagination."""
        filters = (Workspace.owner_id == user_id) | (
            workspace_members.c.user_id == user_id
        )

        base_query = (
            select(Workspace)
            .outerjoin(
                workspace_members,
                Workspace.id == workspace_members.c.workspace_id,
            )
            .where(filters)
            .distinct()
        )

        count_query = select(func.count()).select_from(
            base_query.order_by(None).subquery()
        )
        total = await self.session.scalar(count_query) or 0

        statement = (
            base_query.order_by(Workspace.id).offset((page - 1) * limit).limit(limit)
        )

        result = await self.session.scalars(statement)
        return list(result.all()), total

    async def get_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> WorkspaceRole | None:
        """Get a user's role in a workspace."""
        statement = select(workspace_members.c.role).where(
            workspace_members.c.workspace_id == workspace_id,
            workspace_members.c.user_id == user_id,
        )

        result = await self.session.scalar(statement)

        if result is None:
            return None

        return WorkspaceRole(result)

    async def add_member(
        self,
        workspace_id: int,
        user_id: int,
        role: WorkspaceRole,
    ) -> None:
        """Insert a workspace member."""
        statement = (
            pg_insert(workspace_members)
            .values(
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    workspace_members.c.workspace_id,
                    workspace_members.c.user_id,
                ]
            )
            .returning(workspace_members.c.user_id)
        )

        result = await self.session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise ConflictError(WORKSPACE_MEMBER_ALREADY_EXISTS)

    async def remove_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> bool:
        """Remove a workspace member."""

        statement = (
            delete(workspace_members)
            .where(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
            .returning(workspace_members.c.user_id)
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_workspace_members(
        self,
        workspace_id: int,
    ) -> list[tuple[User, WorkspaceRole]]:
        """Get all members and their roles in a workspace."""
        statement = (
            select(User, workspace_members.c.role)
            .join(
                workspace_members,
                User.id == workspace_members.c.user_id,
            )
            .where(workspace_members.c.workspace_id == workspace_id)
            .order_by(User.id)
        )

        result = await self.session.execute(statement)

        return [(user, WorkspaceRole(role)) for user, role in result.all()]
