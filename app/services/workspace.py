from app.core.constants import DEFAULT_PAGE, DEFAULT_PAGE_LIMIT
from app.core.exceptions import (
    ConflictError,
    InvalidOperation,
    NotFoundException,
)
from app.core.messages import (
    USER_NOT_FOUND,
    WORKSPACE_MEMBER_ALREADY_EXISTS,
    WORKSPACE_MEMBER_NOT_FOUND,
    WORKSPACE_NOT_FOUND,
    WORKSPACE_OWNER_CANNOT_BE_MEMBER,
    WORKSPACE_OWNER_CANNOT_BE_REMOVED,
    WORKSPACE_OWNER_ROLE_INVALID,
)
from app.models import User, WorkspaceRole
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    """Business logic for workspace operations."""

    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        user_repository: UserRepository,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.user_repository = user_repository

    async def create_workspace(
        self,
        data: WorkspaceCreate,
        current_user: User,
    ) -> WorkspaceResponse:
        workspace = await self.workspace_repository.create(
            {"name": data.name, "owner_id": current_user.id}
        )
        return WorkspaceResponse.model_validate(workspace)

    async def get_workspaces(
        self,
        current_user: User,
        page: int = DEFAULT_PAGE,
        limit: int = DEFAULT_PAGE_LIMIT,
    ) -> WorkspaceListResponse:
        workspaces, total = (
            await self.workspace_repository.get_user_workspaces_paginated(
                current_user.id,
                page,
                limit,
            )
        )
        return WorkspaceListResponse(
            items=[
                WorkspaceResponse.model_validate(workspace)
                for workspace in workspaces
            ],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_workspace(
        self,
        workspace_id: int,
    ) -> WorkspaceResponse:
        workspace = await self.workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)
        return WorkspaceResponse.model_validate(workspace)

    async def get_workspace_members(
        self,
        workspace_id: int,
    ) -> list[WorkspaceMemberResponse]:
        workspace = await self.workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

        members = await self.workspace_repository.get_workspace_members(
            workspace_id
        )
        responses = [
            WorkspaceMemberResponse(user_id=user.id, role=role)
            for user, role in members
        ]
        responses.insert(
            0,
            WorkspaceMemberResponse(
                user_id=workspace.owner_id,
                role=WorkspaceRole.OWNER,
            ),
        )
        return responses

    async def update_workspace(
        self,
        workspace_id: int,
        data: WorkspaceUpdate,
    ) -> WorkspaceResponse:
        workspace = await self.workspace_repository.update(
            workspace_id,
            data.model_dump(exclude_unset=True),
        )
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)
        return WorkspaceResponse.model_validate(workspace)

    async def delete_workspace(self, workspace_id: int) -> None:
        deleted = await self.workspace_repository.delete(workspace_id)
        if not deleted:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

    async def add_member(
        self,
        workspace_id: int,
        user_id: int,
        role: WorkspaceRole,
    ) -> WorkspaceMemberResponse:
        workspace = await self.workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

        if role == WorkspaceRole.OWNER:
            raise InvalidOperation(WORKSPACE_OWNER_ROLE_INVALID)

        if workspace.owner_id == user_id:
            raise InvalidOperation(WORKSPACE_OWNER_CANNOT_BE_MEMBER)

        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException(USER_NOT_FOUND)

        existing_role = await self.workspace_repository.get_member(
            workspace_id,
            user_id,
        )
        if existing_role is not None:
            raise ConflictError(WORKSPACE_MEMBER_ALREADY_EXISTS)

        await self.workspace_repository.add_member(
            workspace_id,
            user_id,
            role,
        )
        return WorkspaceMemberResponse(user_id=user_id, role=role)

    async def remove_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> None:
        workspace = await self.workspace_repository.get_by_id(workspace_id)
        if workspace is None:
            raise NotFoundException(WORKSPACE_NOT_FOUND)

        if workspace.owner_id == user_id:
            raise InvalidOperation(WORKSPACE_OWNER_CANNOT_BE_REMOVED)

        removed = await self.workspace_repository.remove_member(
            workspace_id,
            user_id,
        )
        if not removed:
            raise NotFoundException(WORKSPACE_MEMBER_NOT_FOUND)
