from uuid import uuid4

from fastapi.testclient import TestClient


def register_and_login(
    client: TestClient,
    cleanup_user: list[int],
) -> tuple[int, dict[str, str]]:
    email = f"project_{uuid4().hex[:12]}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Project Test User",
            "password": "TestPassword123",
        },
    )
    assert register_response.status_code == 201

    user_id = register_response.json()["id"]
    cleanup_user.append(user_id)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123",
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def create_test_workspace(
    client: TestClient,
    headers: dict[str, str],
    cleanup_workspace: list[int],
) -> int:
    response = client.post(
        "/api/v1/workspaces",
        headers=headers,
        json={"name": "Project Test Workspace"},
    )
    assert response.status_code == 201

    workspace_id = response.json()["id"]

    assert isinstance(workspace_id, int)

    cleanup_workspace.append(workspace_id)
    return workspace_id


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_get_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    create_response = client.post(
        base_url,
        headers=headers,
        json={
            "name": "Website Project",
            "description": "Build company website",
        },
    )

    assert create_response.status_code == 201
    project = create_response.json()
    assert project["name"] == "Website Project"
    assert project["description"] == "Build company website"
    assert project["workspace_id"] == workspace_id

    get_response = client.get(base_url, headers=headers)

    assert get_response.status_code == 200
    assert any(item["id"] == project["id"] for item in get_response.json())


def test_update_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    created = client.post(
        base_url,
        headers=headers,
        json={"name": "Old Name"},
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    response = client.patch(
        f"{base_url}/{project_id}",
        headers=headers,
        json={"name": "New Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    created = client.post(
        base_url,
        headers=headers,
        json={"name": "Delete Me"},
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    response = client.delete(
        f"{base_url}/{project_id}",
        headers=headers,
    )
    assert response.status_code == 204

    get_response = client.get(
        f"{base_url}/{project_id}",
        headers=headers,
    )
    assert get_response.status_code == 404


def test_viewer_can_read_but_cannot_create_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, owner_headers = register_and_login(client, cleanup_user)
    viewer_id, viewer_headers = register_and_login(client, cleanup_user)

    workspace_id = create_test_workspace(
        client,
        owner_headers,
        cleanup_workspace,
    )

    add_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": viewer_id, "role": "VIEWER"},
    )
    assert add_response.status_code == 201

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    create_response = client.post(
        base_url,
        headers=owner_headers,
        json={"name": "Owner Project"},
    )
    assert create_response.status_code == 201

    get_response = client.get(base_url, headers=viewer_headers)
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1

    viewer_create = client.post(
        base_url,
        headers=viewer_headers,
        json={"name": "Viewer Project"},
    )
    assert viewer_create.status_code == 403


def test_editor_can_create_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, owner_headers = register_and_login(client, cleanup_user)
    editor_id, editor_headers = register_and_login(client, cleanup_user)

    workspace_id = create_test_workspace(
        client,
        owner_headers,
        cleanup_workspace,
    )

    add_response = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": editor_id, "role": "EDITOR"},
    )
    assert add_response.status_code == 201

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=editor_headers,
        json={"name": "Editor Project"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Editor Project"


def test_project_routes_require_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/workspaces/1/projects",
    )

    assert response.status_code in (401, 403)


def test_project_validation(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": ""},
    )

    assert response.status_code == 422


def test_viewer_cannot_update_or_delete_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, owner_headers = register_and_login(client, cleanup_user)
    viewer_id, viewer_headers = register_and_login(client, cleanup_user)

    workspace_id = create_test_workspace(client, owner_headers, cleanup_workspace)
    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    created = client.post(
        base_url,
        headers=owner_headers,
        json={"name": "Owner Project"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    added = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": viewer_id, "role": "VIEWER"},
    )
    assert added.status_code == 201

    update = client.patch(
        f"{base_url}/{project_id}",
        headers=viewer_headers,
        json={"name": "Changed"},
    )
    assert update.status_code == 403

    delete_response = client.delete(
        f"{base_url}/{project_id}",
        headers=viewer_headers,
    )
    assert delete_response.status_code == 403


def test_editor_can_update_and_delete_project(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    _, owner_headers = register_and_login(client, cleanup_user)
    editor_id, editor_headers = register_and_login(client, cleanup_user)

    workspace_id = create_test_workspace(client, owner_headers, cleanup_workspace)
    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    added = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": editor_id, "role": "EDITOR"},
    )
    assert added.status_code == 201

    created = client.post(
        base_url,
        headers=owner_headers,
        json={"name": "Owner Project"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    update = client.patch(
        f"{base_url}/{project_id}",
        headers=editor_headers,
        json={"name": "Updated By Editor"},
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Updated By Editor"

    delete_response = client.delete(
        f"{base_url}/{project_id}",
        headers=editor_headers,
    )
    assert delete_response.status_code == 204


def test_update_project_rejects_null_name(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    """A project name cannot be set to null."""

    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    created = client.post(
        base_url,
        headers=headers,
        json={"name": "Original Project Name"},
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    update_response = client.patch(
        f"{base_url}/{project_id}",
        headers=headers,
        json={"name": None},
    )

    assert update_response.status_code == 422

    get_response = client.get(
        f"{base_url}/{project_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Original Project Name"


def test_project_name_rejects_whitespace_only(
    client: TestClient,
    cleanup_user: list[int],
    cleanup_workspace: list[int],
) -> None:
    """Project names containing only whitespace are invalid."""

    _, headers = register_and_login(client, cleanup_user)
    workspace_id = create_test_workspace(
        client,
        headers,
        cleanup_workspace,
    )

    base_url = f"/api/v1/workspaces/{workspace_id}/projects"

    create_response = client.post(
        base_url,
        headers=headers,
        json={"name": "   "},
    )

    assert create_response.status_code == 422

    created = client.post(
        base_url,
        headers=headers,
        json={"name": "Valid Project"},
    )
    assert created.status_code == 201

    project_id = created.json()["id"]

    update_response = client.patch(
        f"{base_url}/{project_id}",
        headers=headers,
        json={"name": "   "},
    )

    assert update_response.status_code == 422

    get_response = client.get(
        f"{base_url}/{project_id}",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Valid Project"
