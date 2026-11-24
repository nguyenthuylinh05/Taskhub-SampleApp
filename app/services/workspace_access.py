"""Shared workspace access resolution and authorization policy."""

from dataclasses import dataclass

from app.core.exceptions import NotFoundException
from app.models import User, UserRole, Workspace, WorkspaceRole
from app.repositories.workspace import WorkspaceRepository


@dataclass
class WorkspaceAccess:
    """Authenticated user's access to a workspace."""

    workspace: Workspace
    role: WorkspaceRole


def has_workspace_write_access(role: WorkspaceRole) -> bool:
    """Return whether a workspace role can modify workspace resources."""

    return role in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR)


async def resolve_workspace_access(
    workspace_id: int,
    current_user: User,
    workspace_repository: WorkspaceRepository,
) -> WorkspaceAccess:
    """Resolve the current user's workspace and effective role."""

    workspace = await workspace_repository.get_by_id(workspace_id)

    if workspace is None:
        raise NotFoundException()

    # System administrators have OWNER-level access.
    if current_user.role == UserRole.ADMIN:
        return WorkspaceAccess(workspace, WorkspaceRole.OWNER)

    # Workspace owners do not need a membership record.
    if workspace.owner_id == current_user.id:
        return WorkspaceAccess(workspace, WorkspaceRole.OWNER)

    role = await workspace_repository.get_member(
        workspace_id,
        current_user.id,
    )

    if role is None:
        raise NotFoundException()

    return WorkspaceAccess(workspace, role)
