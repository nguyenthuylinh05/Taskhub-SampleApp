from collections.abc import Generator
from typing import TypedDict, cast
from uuid import uuid4

import anyio
import pytest
from app.core.config import DATABASE_URL
from app.models import Workspace
from app.models.workspace import workspace_members
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


class RegisteredUser(TypedDict):
    id: int
    email: str
    full_name: str


def register_user(
    client: TestClient,
    cleanup_user: list[int],
) -> RegisteredUser:
    """Register a unique test user."""

    email = f"workspace_{uuid4().hex[:12]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Workspace Test User",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    user_data = response.json()
    cleanup_user.append(user_data["id"])

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "full_name": user_data["full_name"],
    }


def login_user(client: TestClient, user_data: RegisteredUser) -> str:
    """Login a test user and return the access token."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    return cast(str, response.json()["access_token"])


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def cleanup_workspace(
    cleanup_user: list[int],
) -> Generator[list[int], None, None]:
    """Track and remove workspaces created during tests."""

    workspace_ids: list[int] = []

    yield workspace_ids

    if not workspace_ids:
        return

    async def delete_test_workspaces() -> None:
        test_engine = create_async_engine(
            DATABASE_URL,
            poolclass=NullPool,
        )

        session_factory = async_sessionmaker(
            test_engine,
            expire_on_commit=False,
        )

        try:
            async with session_factory() as session:
                await session.execute(
                    delete(workspace_members).where(
                        workspace_members.c.workspace_id.in_(workspace_ids),
                    ),
                )

                await session.execute(
                    delete(Workspace).where(
                        Workspace.id.in_(workspace_ids),
                    ),
                )

                await session.commit()
        finally:
            await test_engine.dispose()

    anyio.run(delete_test_workspaces)


def create_workspace(
    client: TestClient,
    access_token: str,
    cleanup_workspace: list[int],
) -> dict[str, object]:
    """Create a workspace and track its ID for cleanup."""

    response = client.post(
        "/api/v1/workspaces",
        headers=auth_headers(access_token),
        json={"name": "Test Workspace"},
    )

    assert response.status_code == 201

    workspace_data = cast(dict[str, object], response.json())
    workspace_id = cast(int, workspace_data["id"])

    cleanup_workspace.append(workspace_id)

    return workspace_data


def test_create_and_get_workspace(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)

    assert workspace["name"] == "Test Workspace"
    assert workspace["owner_id"] == owner["id"]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == workspace["id"]


def test_get_user_workspaces(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)

    response = client.get(
        "/api/v1/workspaces",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert any(
        item["id"] == workspace["id"]
        for item in response.json()
    )


def test_owner_can_update_and_delete_workspace(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)
    workspace_id = workspace["id"]

    update_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers(token),
        json={"name": "Updated Workspace"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Workspace"

    delete_response = client.delete(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers(token),
    )

    assert delete_response.status_code == 204

    cleanup_workspace.remove(cast(int, workspace_id))

    get_response = client.get(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


def test_owner_can_add_list_and_remove_member(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    member = register_user(client, cleanup_user)

    owner_token = login_user(client, owner)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )
    workspace_id = workspace["id"]

    add_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": member["id"],
            "role": "EDITOR",
        },
    )

    assert add_response.status_code == 201
    assert add_response.json()["user_id"] == member["id"]
    assert add_response.json()["role"] == "EDITOR"

    list_response = client.get(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
    )

    assert list_response.status_code == 200

    members = list_response.json()

    assert any(
        item["user_id"] == owner["id"]
        and item["role"] == "OWNER"
        for item in members
    )

    assert any(
        item["user_id"] == member["id"]
        and item["role"] == "EDITOR"
        for item in members
    )

    remove_response = client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{member['id']}",
        headers=auth_headers(owner_token),
    )

    assert remove_response.status_code == 204


def test_viewer_cannot_update_workspace(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    viewer = register_user(client, cleanup_user)

    owner_token = login_user(client, owner)
    viewer_token = login_user(client, viewer)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )
    workspace_id = workspace["id"]

    add_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": viewer["id"],
            "role": "VIEWER",
        },
    )

    assert add_response.status_code == 201

    response = client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        headers=auth_headers(viewer_token),
        json={"name": "Changed By Viewer"},
    )

    assert response.status_code == 403


def test_editor_cannot_manage_workspace_members(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    editor = register_user(client, cleanup_user)
    another_user = register_user(client, cleanup_user)

    owner_token = login_user(client, owner)
    editor_token = login_user(client, editor)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )
    workspace_id = workspace["id"]

    add_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": editor["id"],
            "role": "EDITOR",
        },
    )

    assert add_response.status_code == 201

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(editor_token),
        json={
            "user_id": another_user["id"],
            "role": "VIEWER",
        },
    )

    assert response.status_code == 403


def test_non_member_cannot_access_workspace(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    outsider = register_user(client, cleanup_user)

    owner_token = login_user(client, owner)
    outsider_token = login_user(client, outsider)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(outsider_token),
    )

    assert response.status_code == 404


def test_unauthenticated_user_cannot_access_workspaces(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/workspaces")

    assert response.status_code in (401, 403)


def test_owner_cannot_be_added_as_workspace_member(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    owner_token = login_user(client, owner)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={
            "user_id": owner["id"],
            "role": "VIEWER",
        },
    )

    assert response.status_code == 400


def test_owner_cannot_be_removed_from_workspace(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    owner_token = login_user(client, owner)

    workspace = create_workspace(
        client,
        owner_token,
        cleanup_workspace,
    )

    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{owner['id']}",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 400


def test_update_workspace_with_null_name_returns_422(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(token),
        json={"name": None},
    )

    assert response.status_code == 422


def test_update_workspace_without_name_keeps_existing_name(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        headers=auth_headers(token),
        json={},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Workspace"


def test_remove_nonexistent_member_returns_404(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    token = login_user(client, owner)

    workspace = create_workspace(client, token, cleanup_workspace)

    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_cannot_add_duplicate_workspace_member(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    owner = register_user(client, cleanup_user)
    member = register_user(client, cleanup_user)

    owner_token = login_user(client, owner)

    workspace = create_workspace(client, owner_token, cleanup_workspace)
    workspace_id = workspace["id"]

    payload = {
        "user_id": member["id"],
        "role": "EDITOR",
    }

    first_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=auth_headers(owner_token),
        json=payload,
    )

    assert second_response.status_code == 409