from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import (
    InactiveUser,
    InvalidCredentials,
    PermissionDenied,
    ResourceNotFound,
)
from app.core.security import decode_token
from app.models import User, UserRole, Workspace, WorkspaceRole, workspace_members
from app.repositories.user import UserRepository

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

    except (jwt.InvalidTokenError, ValueError):
        raise InvalidCredentials() from None

    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(user_id_int)

    if user is None:
        raise InvalidCredentials()

    if not user.is_active:
        raise InactiveUser()

    return user

async def get_workspace_role(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkspaceRole:
    """Get the current user's role in a workspace."""

    workspace = await session.get(Workspace, workspace_id)

    if workspace is None:
        raise ResourceNotFound()

    # System administrator has access to every workspace.
    if current_user.role == UserRole.ADMIN:
        return WorkspaceRole.OWNER

    # Workspace owner does not need a membership record.
    if workspace.owner_id == current_user.id:
        return WorkspaceRole.OWNER

    statement = select(workspace_members.c.role).where(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id,
    )

    result = await session.execute(statement)
    role = result.scalar_one_or_none()

    if role is None:
        raise ResourceNotFound()

    return WorkspaceRole(role)

async def require_workspace_member(
    workspace_role: Annotated[
        WorkspaceRole,
        Depends(get_workspace_role),
    ],
) -> WorkspaceRole:
    """Require the user to be a workspace member."""
    return workspace_role


async def require_workspace_editor(
    workspace_role: Annotated[
        WorkspaceRole,
        Depends(get_workspace_role),
    ],
) -> WorkspaceRole:
    """Require OWNER or EDITOR role."""
    if workspace_role not in (
        WorkspaceRole.OWNER,
        WorkspaceRole.EDITOR,
    ):
        raise PermissionDenied()

    return workspace_role


async def require_workspace_owner(
    workspace_role: Annotated[
        WorkspaceRole,
        Depends(get_workspace_role),
    ],
) -> WorkspaceRole:
    """Require OWNER role."""
    if workspace_role != WorkspaceRole.OWNER:
        raise PermissionDenied()

    return workspace_role


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require system administrator role."""

    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied()

    return current_user