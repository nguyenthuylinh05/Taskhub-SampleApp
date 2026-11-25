"""Label management API tests."""

from collections.abc import Callable

from fastapi.testclient import TestClient


def create_project(
    client: TestClient,
    headers: dict[str, str],
    workspace_id: int,
    name: str = "Label Test Project",
) -> int:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/projects",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201
    project_id = response.json()["id"]
    assert isinstance(project_id, int)
    return project_id


def create_task(
    client: TestClient,
    headers: dict[str, str],
    project_id: int,
) -> int:
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Label test task"},
    )
    assert response.status_code == 201
    task_id = response.json()["id"]
    assert isinstance(task_id, int)
    return task_id


def test_label_crud_and_task_association(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_project(client, headers, workspace_id)
    task_id = create_task(client, headers, project_id)
    project_labels_url = f"/api/v1/projects/{project_id}/labels"

    created = client.post(
        project_labels_url,
        headers=headers,
        json={"name": "Urgent", "color": "#FF3300"},
    )
    assert created.status_code == 201
    label = created.json()
    label_id = label["id"]
    assert label == {
        "id": label_id,
        "project_id": project_id,
        "name": "Urgent",
        "color": "#FF3300",
    }

    listed = client.get(project_labels_url, headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [label_id]

    retrieved = client.get(f"/api/v1/labels/{label_id}", headers=headers)
    assert retrieved.status_code == 200
    assert retrieved.json()["name"] == "Urgent"

    updated = client.patch(
        f"/api/v1/labels/{label_id}",
        headers=headers,
        json={"name": "Critical", "color": "#AA00CC"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Critical"
    assert updated.json()["color"] == "#AA00CC"

    assignment_url = f"/api/v1/tasks/{task_id}/labels/{label_id}"
    assigned = client.post(assignment_url, headers=headers)
    assert assigned.status_code == 204

    duplicate = client.post(assignment_url, headers=headers)
    assert duplicate.status_code == 409

    removed = client.delete(assignment_url, headers=headers)
    assert removed.status_code == 204

    # Removing an association leaves the project label available.
    assert client.get(f"/api/v1/labels/{label_id}", headers=headers).status_code == 200

    # Deleting a label with associations removes those associations safely.
    assert client.post(assignment_url, headers=headers).status_code == 204
    deleted = client.delete(f"/api/v1/labels/{label_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/labels/{label_id}", headers=headers).status_code == 404


def test_labels_reject_invalid_and_missing_resources(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_project(client, headers, workspace_id)

    invalid_name = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=headers,
        json={"name": "   ", "color": "#112233"},
    )
    assert invalid_name.status_code == 422

    invalid_color = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=headers,
        json={"name": "Valid", "color": "red"},
    )
    assert invalid_color.status_code == 422

    missing_project_labels = client.get(
        "/api/v1/projects/999999/labels",
        headers=headers,
    )
    assert missing_project_labels.status_code == 404
    assert client.get("/api/v1/labels/999999", headers=headers).status_code == 404
    assert client.patch(
        "/api/v1/labels/999999",
        headers=headers,
        json={"name": "Missing"},
    ).status_code == 404
    assert client.delete("/api/v1/labels/999999", headers=headers).status_code == 404
    assert client.post(
        "/api/v1/tasks/999999/labels/1",
        headers=headers,
    ).status_code == 404
    assert client.delete(
        "/api/v1/tasks/999999/labels/1",
        headers=headers,
    ).status_code == 404


def test_labels_cannot_cross_projects_or_workspace_access(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_one = create_project(client, owner_headers, workspace_id)
    project_two = create_project(client, owner_headers, workspace_id, "Other")
    task_id = create_task(client, owner_headers, project_one)
    label = client.post(
        f"/api/v1/projects/{project_two}/labels",
        headers=owner_headers,
        json={"name": "External", "color": "#112233"},
    )
    assert label.status_code == 201

    cross_project = client.post(
        f"/api/v1/tasks/{task_id}/labels/{label.json()['id']}",
        headers=owner_headers,
    )
    assert cross_project.status_code == 400

    hidden = client.get(
        f"/api/v1/projects/{project_one}/labels",
        headers=outsider_headers,
    )
    assert hidden.status_code == 404


def test_viewer_is_read_only_for_labels(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, owner_headers = register_and_login()
    viewer_id, viewer_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_project(client, owner_headers, workspace_id)
    task_id = create_task(client, owner_headers, project_id)
    added = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": viewer_id, "role": "VIEWER"},
    )
    assert added.status_code == 201
    label = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=owner_headers,
        json={"name": "Read only", "color": "#112233"},
    ).json()

    assert client.get(
        f"/api/v1/projects/{project_id}/labels",
        headers=viewer_headers,
    ).status_code == 200
    assert client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=viewer_headers,
        json={"name": "Denied", "color": "#112233"},
    ).status_code == 403
    assert client.patch(
        f"/api/v1/labels/{label['id']}",
        headers=viewer_headers,
        json={"name": "Denied"},
    ).status_code == 403
    assert client.delete(
        f"/api/v1/labels/{label['id']}",
        headers=viewer_headers,
    ).status_code == 403
    association_url = f"/api/v1/tasks/{task_id}/labels/{label['id']}"
    assert client.post(association_url, headers=viewer_headers).status_code == 403
    assert client.delete(association_url, headers=viewer_headers).status_code == 403


def test_editor_can_manage_labels(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, owner_headers = register_and_login()
    editor_id, editor_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_project(client, owner_headers, workspace_id)
    member = client.post(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=owner_headers,
        json={"user_id": editor_id, "role": "EDITOR"},
    )
    assert member.status_code == 201

    created = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=editor_headers,
        json={"name": "Editor label", "color": "#112233"},
    )
    assert created.status_code == 201
    assert client.patch(
        f"/api/v1/labels/{created.json()['id']}",
        headers=editor_headers,
        json={"name": "Updated by editor"},
    ).status_code == 200


def test_admin_has_owner_level_label_access(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    promote_to_admin: Callable[[int], None],
) -> None:
    _, owner_headers = register_and_login()
    admin_id, admin_headers = register_and_login()
    promote_to_admin(admin_id)
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_project(client, owner_headers, workspace_id)

    created = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=admin_headers,
        json={"name": "Admin label", "color": "#112233"},
    )
    assert created.status_code == 201
    assert client.get(
        f"/api/v1/projects/{project_id}/labels",
        headers=admin_headers,
    ).status_code == 200

