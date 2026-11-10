from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.api.dependencies import (
    get_workspace_role,
    require_workspace_editor,
    require_workspace_member,
    require_workspace_owner,
)
from app.core.exceptions import PermissionDenied, ResourceNotFound
from app.models import User, UserRole, Workspace, WorkspaceRole
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_admin_has_owner_role() -> None:
    user = cast(
        User,
        SimpleNamespace(id=1, role=UserRole.ADMIN),
    )
    workspace = cast(
        Workspace,
        SimpleNamespace(id=10, owner_id=2),
    )

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.get.return_value = workspace
    session = cast(AsyncSession, session_mock)

    role = await get_workspace_role(
        workspace_id=10,
        current_user=user,
        session=session,
    )

    assert role == WorkspaceRole.OWNER
    session_mock.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_workspace_owner_has_owner_role() -> None:
    user = cast(
        User,
        SimpleNamespace(id=1, role=UserRole.MEMBER),
    )
    workspace = cast(
        Workspace,
        SimpleNamespace(id=10, owner_id=1),
    )

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.get.return_value = workspace
    session = cast(AsyncSession, session_mock)

    role = await get_workspace_role(
        workspace_id=10,
        current_user=user,
        session=session,
    )

    assert role == WorkspaceRole.OWNER
    session_mock.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_workspace_member_gets_membership_role() -> None:
    user = cast(
        User,
        SimpleNamespace(id=2, role=UserRole.MEMBER),
    )
    workspace = cast(
        Workspace,
        SimpleNamespace(id=10, owner_id=1),
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = WorkspaceRole.EDITOR

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.get.return_value = workspace
    session_mock.execute.return_value = result
    session = cast(AsyncSession, session_mock)

    role = await get_workspace_role(
        workspace_id=10,
        current_user=user,
        session=session,
    )

    assert role == WorkspaceRole.EDITOR
    session_mock.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_member_cannot_access_workspace() -> None:
    user = cast(
        User,
        SimpleNamespace(id=3, role=UserRole.MEMBER),
    )
    workspace = cast(
        Workspace,
        SimpleNamespace(id=10, owner_id=1),
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.get.return_value = workspace
    session_mock.execute.return_value = result
    session = cast(AsyncSession, session_mock)

    with pytest.raises(ResourceNotFound):
        await get_workspace_role(
            workspace_id=10,
            current_user=user,
            session=session,
        )


@pytest.mark.asyncio
async def test_nonexistent_workspace_returns_not_found() -> None:
    user = cast(
        User,
        SimpleNamespace(id=1, role=UserRole.MEMBER),
    )

    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.get.return_value = None
    session = cast(AsyncSession, session_mock)

    with pytest.raises(ResourceNotFound):
        await get_workspace_role(
            workspace_id=999,
            current_user=user,
            session=session,
        )

    session_mock.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_viewer_can_read_workspace() -> None:
    role = await require_workspace_member(WorkspaceRole.VIEWER)

    assert role == WorkspaceRole.VIEWER


@pytest.mark.asyncio
async def test_editor_can_edit_workspace() -> None:
    role = await require_workspace_editor(WorkspaceRole.EDITOR)

    assert role == WorkspaceRole.EDITOR


@pytest.mark.asyncio
async def test_viewer_cannot_edit_workspace() -> None:
    with pytest.raises(PermissionDenied):
        await require_workspace_editor(WorkspaceRole.VIEWER)


@pytest.mark.asyncio
async def test_editor_cannot_manage_workspace() -> None:
    with pytest.raises(PermissionDenied):
        await require_workspace_owner(WorkspaceRole.EDITOR)


@pytest.mark.asyncio
async def test_owner_can_manage_workspace() -> None:
    role = await require_workspace_owner(WorkspaceRole.OWNER)

    assert role == WorkspaceRole.OWNER
