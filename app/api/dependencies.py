from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import WorkspaceRepositoryDep
from app.core.exceptions import (
    InactiveUser,
    InvalidCredentials,
    NotFoundException,
    PermissionDenied,
)
from app.core.security import decode_token
from app.models import User, UserRole, Workspace, WorkspaceRole
from app.repositories.user import UserRepository


@dataclass
class WorkspaceAccess:
    """Authenticated user's access to a workspace."""

    workspace: Workspace
    role: WorkspaceRole


bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Get the authenticated active user from an access token."""

    try:
        payload = decode_token(credentials.credentials)

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not isinstance(user_id, str) or token_type != "access":
            raise InvalidCredentials()

        user_id_int = int(user_id)

        if user_id_int <= 0:
            raise InvalidCredentials()

    except (jwt.InvalidTokenError, ValueError):
        raise InvalidCredentials() from None

    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(user_id_int)

    if user is None:
        raise InvalidCredentials()

    if not user.is_active:
        raise InactiveUser()

    return user


CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]


async def get_workspace_access(
    workspace_id: int,
    current_user: CurrentUserDep,
    workspace_repository: WorkspaceRepositoryDep,
) -> WorkspaceAccess:
    """Get the current user's access to a workspace."""

    workspace = await workspace_repository.get_by_id(workspace_id)

    if workspace is None:
        raise NotFoundException()

    # System administrator has access to every workspace.
    if current_user.role == UserRole.ADMIN:
        return WorkspaceAccess(workspace, WorkspaceRole.OWNER)

    # Workspace owner does not need a membership record.
    if workspace.owner_id == current_user.id:
        return WorkspaceAccess(workspace, WorkspaceRole.OWNER)

    role = await workspace_repository.get_member(
        workspace_id,
        current_user.id,
    )

    if role is None:
        raise NotFoundException()

    return WorkspaceAccess(workspace, role)


async def require_workspace_member(
    workspace_access: Annotated[
        WorkspaceAccess,
        Depends(get_workspace_access),
    ],
) -> WorkspaceAccess:
    """Require the user to be a workspace member."""

    return workspace_access


async def require_workspace_editor(
    workspace_access: Annotated[
        WorkspaceAccess,
        Depends(get_workspace_access),
    ],
) -> WorkspaceAccess:
    """Require OWNER or EDITOR role."""

    if workspace_access.role not in (
        WorkspaceRole.OWNER,
        WorkspaceRole.EDITOR,
    ):
        raise PermissionDenied()

    return workspace_access


async def require_workspace_owner(
    workspace_access: Annotated[
        WorkspaceAccess,
        Depends(get_workspace_access),
    ],
) -> WorkspaceAccess:
    """Require OWNER role."""

    if workspace_access.role != WorkspaceRole.OWNER:
        raise PermissionDenied()

    return workspace_access


async def require_admin(
    current_user: CurrentUserDep,
) -> User:
    """Require system administrator role."""

    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied()

    return current_user
