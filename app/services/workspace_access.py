"""Shared workspace access resolution and authorization policy."""

from dataclasses import dataclass

from app.core.exceptions import (
    InvalidOperation,
    NotFoundException,
    PermissionDenied,
)
from app.core.messages import PROJECT_ARCHIVED, PROJECT_NOT_FOUND
from app.models import Project, User, UserRole, Workspace, WorkspaceRole
from app.models.enums import ProjectStatus
from app.repositories.project import ProjectRepository
from app.repositories.workspace import WorkspaceRepository


@dataclass
class WorkspaceAccess:
    """Authenticated user's access to a workspace."""

    workspace: Workspace
    role: WorkspaceRole


def has_workspace_write_access(role: WorkspaceRole) -> bool:
    """Return whether a workspace role can modify workspace resources."""

    return role in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR)


async def resolve_project_access(
    project_id: int,
    current_user: User,
    project_repository: ProjectRepository,
    workspace_repository: WorkspaceRepository,
    *,
    require_write: bool = False,
    not_found_message: str = PROJECT_NOT_FOUND,
    inaccessible_message: str | None = None,
) -> tuple[Project, WorkspaceAccess]:
    """Resolve a project and enforce its workspace access policy."""

    project = await project_repository.get_by_id(project_id)
    if project is None:
        raise NotFoundException(not_found_message)

    try:
        access = await resolve_workspace_access(
            project.workspace_id,
            current_user,
            workspace_repository,
        )
    except NotFoundException:
        if inaccessible_message is None:
            raise
        raise NotFoundException(inaccessible_message) from None

    if require_write and not has_workspace_write_access(access.role):
        raise PermissionDenied()

    return project, access


def ensure_project_active(project: Project) -> None:
    """Reject writes to an archived project."""

    if project.status == ProjectStatus.ARCHIVED:
        raise InvalidOperation(PROJECT_ARCHIVED)


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
