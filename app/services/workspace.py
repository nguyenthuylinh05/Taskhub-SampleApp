from app.core.exceptions import (
    ConflictError,
    InvalidOperation,
    NotFoundException,
)
from app.models import User, WorkspaceRole
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
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
        """Create a workspace owned by the current user."""

        workspace = await self.workspace_repository.create(
            {
                "name": data.name,
                "owner_id": current_user.id,
            }
        )

        return WorkspaceResponse.model_validate(workspace)

    async def get_workspaces(
        self,
        current_user: User,
    ) -> list[WorkspaceResponse]:
        """Get workspaces owned or joined by the current user."""

        workspaces = await self.workspace_repository.get_user_workspaces(
            current_user.id
        )

        return [
            WorkspaceResponse.model_validate(workspace)
            for workspace in workspaces
        ]

    async def get_workspace(
        self,
        workspace_id: int,
    ) -> WorkspaceResponse:
        """Get a workspace by ID."""

        workspace = await self.workspace_repository.get_by_id(workspace_id)

        if workspace is None:
            raise NotFoundException()

        return WorkspaceResponse.model_validate(workspace)

    async def update_workspace(
        self,
        workspace_id: int,
        data: WorkspaceUpdate,
    ) -> WorkspaceResponse:
        """Update a workspace."""

        workspace = await self.workspace_repository.update(
            workspace_id,
            data.model_dump(exclude_unset=True),
        )

        if workspace is None:
            raise NotFoundException()

        return WorkspaceResponse.model_validate(workspace)

    async def delete_workspace(self, workspace_id: int) -> None:
        """Delete a workspace."""

        deleted = await self.workspace_repository.delete(workspace_id)

        if not deleted:
            raise NotFoundException()

    async def add_member(
        self,
        workspace_id: int,
        user_id: int,
        role: WorkspaceRole,
    ) -> WorkspaceMemberResponse:
        """Add a user to a workspace."""

        workspace = await self.workspace_repository.get_by_id(workspace_id)

        if workspace is None:
            raise NotFoundException()

        if role == WorkspaceRole.OWNER:
            raise InvalidOperation("Workspace owner cannot be addedas a member")

        user = await self.user_repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException()

        existing_role = await self.workspace_repository.get_member(
            workspace_id,
            user_id,
        )

        if existing_role is not None:
            raise ConflictError("User is already a workspace member")

        if workspace.owner_id == user_id:
            raise InvalidOperation("Workspace owner cannot be assigned as a member")

        await self.workspace_repository.add_member(
            workspace_id,
            user_id,
            role,
        )

        return WorkspaceMemberResponse(
            user_id=user_id,
            role=role,
        )

    async def remove_member(
        self,
        workspace_id: int,
        user_id: int,
    ) -> None:
        """Remove a user from a workspace."""

        workspace = await self.workspace_repository.get_by_id(workspace_id)

        if workspace is None:
            raise NotFoundException()

        if workspace.owner_id == user_id:
            raise InvalidOperation("Workspace owner cannot be removed")

        removed = await self.workspace_repository.remove_member(
            workspace_id,
            user_id,
        )

        if not removed:
            raise NotFoundException()
