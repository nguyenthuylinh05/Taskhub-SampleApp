from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.core.messages import PROJECT_ARCHIVED
from fastapi.testclient import TestClient


def future_due_date() -> str:
    """Return an aware due date safely in the future for validation tests."""

    return (datetime.now(UTC) + timedelta(days=30)).isoformat()


def test_create_and_list_tasks(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Create tasks and list them in a project."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    url = f"/api/v1/projects/{project_id}/tasks"

    create_response = client.post(
        url,
        headers=headers,
        json={
            "title": "Implement authentication",
            "description": "Implement JWT authentication",
        },
    )

    assert create_response.status_code == 201

    task = create_response.json()
    assert task["title"] == "Implement authentication"
    assert task["description"] == "Implement JWT authentication"
    assert task["project_id"] == project_id
    assert task["status"] == "TODO"
    assert task["priority"] == "MEDIUM"
    assert task["assignee_id"] is None

    list_response = client.get(url, headers=headers)

    assert list_response.status_code == 200
    tasks = list_response.json()
    assert tasks["total"] == 1
    assert len(tasks["items"]) == 1
    assert tasks["items"][0]["id"] == task["id"]


def test_update_task_and_assign_workspace_member(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """Update task fields and assign a workspace member."""

    _, owner_headers = register_and_login()
    member_id, _ = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    add_workspace_member(
        owner_headers,
        workspace_id,
        member_id,
        "EDITOR",
    )

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Original task"},
    )
    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={
            "title": "Updated task",
            "description": "Updated description",
            "assignee_id": member_id,
            "status": "IN_PROGRESS",
            "priority": "HIGH",
            "due_date": future_due_date(),
        },
    )

    assert update_response.status_code == 200

    task = update_response.json()
    assert task["title"] == "Updated task"
    assert task["description"] == "Updated description"
    assert task["assignee_id"] == member_id
    assert task["status"] == "IN_PROGRESS"
    assert task["priority"] == "HIGH"
    assert task["due_date"] is not None


def test_unassign_workspace_member_from_task(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """An assigned workspace member can be removed from a task."""

    _, owner_headers = register_and_login()
    member_id, _ = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    add_workspace_member(
        owner_headers,
        workspace_id,
        member_id,
        "EDITOR",
    )

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Task to unassign",
            "assignee_id": member_id,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["assignee_id"] == member_id

    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"assignee_id": None},
    )

    assert update_response.status_code == 200
    assert update_response.json()["assignee_id"] is None


def test_delete_task(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Delete a task from a project."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task to delete"},
    )
    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["total"] == 0
    assert all(task["id"] != task_id for task in get_response.json()["items"])


def test_viewer_can_read_but_cannot_modify_tasks(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """A viewer can list tasks but cannot create, update, or delete them."""

    _, owner_headers = register_and_login()
    viewer_id, viewer_headers = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    add_workspace_member(
        owner_headers,
        workspace_id,
        viewer_id,
        "VIEWER",
    )

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Owner task"},
    )
    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    list_response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=viewer_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert len(list_response.json()["items"]) == 1

    create_by_viewer = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=viewer_headers,
        json={"title": "Viewer task"},
    )
    assert create_by_viewer.status_code == 403

    update_by_viewer = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=viewer_headers,
        json={"title": "Changed by viewer"},
    )
    assert update_by_viewer.status_code == 403

    delete_by_viewer = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=viewer_headers,
    )
    assert delete_by_viewer.status_code == 403


def test_editor_can_create_update_and_delete_tasks(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """An editor can manage tasks in the workspace."""

    _, owner_headers = register_and_login()
    _, editor_headers = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    editor_id = client.get(
        "/api/v1/users/me",
        headers=editor_headers,
    ).json()["id"]

    add_workspace_member(
        owner_headers,
        workspace_id,
        editor_id,
        "EDITOR",
    )

    url = f"/api/v1/projects/{project_id}/tasks"

    create_response = client.post(
        url,
        headers=editor_headers,
        json={"title": "Task created by editor"},
    )
    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=editor_headers,
        json={"title": "Task updated by editor"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Task updated by editor"

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=editor_headers,
    )
    assert delete_response.status_code == 204


def test_task_assignee_must_belong_to_workspace(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """A user outside the workspace cannot be assigned to a task."""

    _, owner_headers = register_and_login()
    outsider_id, _ = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Invalid assignment",
            "assignee_id": outsider_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Task assignee must be a workspace member")


def test_nonexistent_assignee_returns_bad_request(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """An assignee ID that does not exist returns 400."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={
            "title": "Task with nonexistent assignee",
            "assignee_id": 99999999,
        },
    )

    assert response.status_code == 400


def test_task_endpoints_return_not_found_for_missing_resources(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
) -> None:
    """Missing projects and tasks return 404."""

    _, headers = register_and_login()

    missing_project_response = client.get(
        "/api/v1/projects/999999/tasks",
        headers=headers,
    )
    assert missing_project_response.status_code == 404

    missing_task_update = client.patch(
        "/api/v1/tasks/999999",
        headers=headers,
        json={"title": "Missing task"},
    )
    assert missing_task_update.status_code == 404

    missing_task_delete = client.delete(
        "/api/v1/tasks/999999",
        headers=headers,
    )
    assert missing_task_delete.status_code == 404


def test_task_validation(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Validate task fields, due dates, and empty updates."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    url = f"/api/v1/projects/{project_id}/tasks"

    empty_title = client.post(
        url,
        headers=headers,
        json={"title": ""},
    )
    assert empty_title.status_code == 422

    invalid_priority = client.post(
        url,
        headers=headers,
        json={
            "title": "Invalid priority",
            "priority": "CRITICAL",
        },
    )
    assert invalid_priority.status_code == 422

    created = client.post(
        url,
        headers=headers,
        json={
            "title": "Valid task",
            "description": "Description to clear",
        },
    )
    assert created.status_code == 201

    task_id = created.json()["id"]

    empty_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={},
    )
    assert empty_update.status_code == 422

    null_title = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"title": None},
    )
    assert null_title.status_code == 422

    null_status = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"status": None},
    )
    assert null_status.status_code == 422

    null_priority = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"priority": None},
    )
    assert null_priority.status_code == 422

    null_description = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"description": None},
    )
    assert null_description.status_code == 200
    assert null_description.json()["description"] is None

    null_assignee = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"assignee_id": None},
    )
    assert null_assignee.status_code == 200
    assert null_assignee.json()["assignee_id"] is None

    # Timezone-aware due date is accepted.
    valid_due_date = client.post(
        url,
        headers=headers,
        json={
            "title": "Task with timezone",
            "due_date": future_due_date(),
        },
    )
    assert valid_due_date.status_code == 201

    # Timezone-naive due date is rejected.
    invalid_due_date = client.post(
        url,
        headers=headers,
        json={
            "title": "Task without timezone",
            "due_date": "2026-12-01T10:00:00",
        },
    )
    assert invalid_due_date.status_code == 422

    # Past due date is rejected.
    past_due_date = client.post(
        url,
        headers=headers,
        json={
            "title": "Task with past due date",
            "due_date": "2020-01-01T10:00:00+07:00",
        },
    )
    assert past_due_date.status_code == 422

    # Timezone-aware due date can be updated.
    valid_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"due_date": future_due_date()},
    )
    assert valid_update.status_code == 200

    # Timezone-naive due date cannot be updated.
    invalid_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"due_date": "2026-12-15T15:30:00"},
    )
    assert invalid_update.status_code == 422

    # Past due date cannot be used when updating a task.
    past_due_date_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"due_date": "2020-01-01T10:00:00+07:00"},
    )
    assert past_due_date_update.status_code == 422

    # Due date can be cleared with null.
    clear_due_date = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"due_date": None},
    )
    assert clear_due_date.status_code == 200
    assert clear_due_date.json()["due_date"] is None


def test_filter_tasks_by_status(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Filter project tasks by status."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    url = f"/api/v1/projects/{project_id}/tasks"

    for title, task_status in [
        ("Todo task", "TODO"),
        ("In progress task", "IN_PROGRESS"),
        ("Done task", "DONE"),
    ]:
        response = client.post(
            url,
            headers=headers,
            json={"title": title},
        )
        assert response.status_code == 201

        update_response = client.patch(
            f"/api/v1/tasks/{response.json()['id']}",
            headers=headers,
            json={"status": task_status},
        )
        assert update_response.status_code == 200

    response = client.get(
        url,
        headers=headers,
        params={"status": "IN_PROGRESS"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "In progress task"
    assert result["items"][0]["status"] == "IN_PROGRESS"


def test_filter_tasks_by_priority_and_assignee(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """Filter tasks by priority and assignee together."""

    _, owner_headers = register_and_login()
    assignee_id, _ = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    add_workspace_member(
        owner_headers,
        workspace_id,
        assignee_id,
        "EDITOR",
    )

    url = f"/api/v1/projects/{project_id}/tasks"

    for title, priority, assignee in [
        ("Matching task", "HIGH", assignee_id),
        ("Wrong priority", "LOW", assignee_id),
        ("Wrong assignee", "HIGH", None),
    ]:
        response = client.post(
            url,
            headers=owner_headers,
            json={
                "title": title,
                "priority": priority,
                "assignee_id": assignee,
            },
        )
        assert response.status_code == 201

    response = client.get(
        url,
        headers=owner_headers,
        params={
            "priority": "HIGH",
            "assignee_id": assignee_id,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Matching task"


def test_task_pagination(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Return the requested page and total matching task count."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    url = f"/api/v1/projects/{project_id}/tasks"

    for index in range(5):
        response = client.post(
            url,
            headers=headers,
            json={"title": f"Pagination task {index}"},
        )
        assert response.status_code == 201

    response = client.get(
        url,
        headers=headers,
        params={"page": 2, "limit": 2},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 5
    assert result["page"] == 2
    assert result["limit"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["title"] == "Pagination task 2"
    assert result["items"][1]["title"] == "Pagination task 3"


def test_task_pagination_empty_page(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """An out-of-range page returns an empty item list."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    url = f"/api/v1/projects/{project_id}/tasks"

    response = client.post(
        url,
        headers=headers,
        json={"title": "Only task"},
    )
    assert response.status_code == 201

    response = client.get(
        url,
        headers=headers,
        params={"page": 5, "limit": 10},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 1
    assert result["items"] == []
    assert result["page"] == 5
    assert result["limit"] == 10


def test_task_pagination_validation(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Reject invalid pagination parameters."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    url = f"/api/v1/projects/{project_id}/tasks"

    for params in [
        {"page": 0},
        {"limit": 0},
        {"limit": 101},
    ]:
        response = client.get(
            url,
            headers=headers,
            params=params,
        )
        assert response.status_code == 422


def test_non_member_cannot_list_project_tasks(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """A user outside the workspace cannot list its project tasks."""

    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=outsider_headers,
    )

    assert response.status_code == 404


def test_non_member_cannot_create_update_or_delete_tasks(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """A user outside the workspace cannot modify its tasks."""

    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Owner task"},
    )
    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    create_by_outsider = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=outsider_headers,
        json={"title": "Outsider task"},
    )
    assert create_by_outsider.status_code == 404

    update_by_outsider = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=outsider_headers,
        json={"title": "Changed by outsider"},
    )
    assert update_by_outsider.status_code == 404

    delete_by_outsider = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=outsider_headers,
    )
    assert delete_by_outsider.status_code == 404

    owner_get_response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
    )
    assert owner_get_response.status_code == 200
    assert owner_get_response.json()["total"] == 1
    assert owner_get_response.json()["items"][0]["id"] == task_id


def test_viewer_cannot_be_assigned_to_task(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    """A viewer cannot be assigned to a task."""

    _, owner_headers = register_and_login()
    viewer_id, _ = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    add_workspace_member(
        owner_headers,
        workspace_id,
        viewer_id,
        "VIEWER",
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={
            "title": "Task assigned to viewer",
            "assignee_id": viewer_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Task assignee must be a workspace owner or editor"
    )


def test_cannot_create_task_in_archived_project(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """An archived project does not allow task creation."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    archive_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archive_response.status_code == 200

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task in archived project"},
    )

    assert create_response.status_code == 400
    assert create_response.json()["detail"] == PROJECT_ARCHIVED


def test_cannot_update_task_in_archived_project(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """An archived project does not allow task updates."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Original task"},
    )
    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    archive_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archive_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"title": "Updated task"},
    )

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == PROJECT_ARCHIVED


def test_cannot_delete_task_in_archived_project(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """An archived project does not allow task deletion."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Task to preserve"},
    )
    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    archive_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archive_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
    )

    assert delete_response.status_code == 400
    assert delete_response.json()["detail"] == PROJECT_ARCHIVED


def test_can_list_tasks_in_archived_project(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """Workspace members can still list tasks in archived projects."""

    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Existing task"},
    )
    assert task_response.status_code == 201

    task_id = task_response.json()["id"]

    archive_response = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archive_response.status_code == 200

    list_response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
    )

    assert list_response.status_code == 200
    result = list_response.json()
    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == task_id


def test_admin_can_access_tasks_without_workspace_membership(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    promote_to_admin: Callable[[int], None],
) -> None:
    """An admin can access workspace tasks without membership."""

    _, owner_headers = register_and_login()
    admin_id, admin_headers = register_and_login()

    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Task created by workspace owner"},
    )
    assert task_response.status_code == 201

    promote_to_admin(admin_id)

    # Admin is not a workspace member but has system-wide access.
    list_response = client.get(
        f"/api/v1/projects/{project_id}/tasks",
        headers=admin_headers,
    )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    create_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=admin_headers,
        json={"title": "Task created by admin"},
    )

    assert create_response.status_code == 201


def test_member_cannot_access_tasks_from_another_workspace(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    """A workspace member cannot access tasks from another workspace."""

    _, owner_a_headers = register_and_login()
    _, owner_b_headers = register_and_login()

    # Create two independent workspaces and projects.
    workspace_a_id = create_test_workspace(owner_a_headers)
    workspace_b_id = create_test_workspace(owner_b_headers)

    project_a_id = create_test_project(
        owner_a_headers,
        workspace_a_id,
    )
    project_b_id = create_test_project(
        owner_b_headers,
        workspace_b_id,
    )

    # Create one task in each workspace.
    task_a_response = client.post(
        f"/api/v1/projects/{project_a_id}/tasks",
        headers=owner_a_headers,
        json={"title": "Task in workspace A"},
    )
    assert task_a_response.status_code == 201
    task_a_id = task_a_response.json()["id"]

    task_b_response = client.post(
        f"/api/v1/projects/{project_b_id}/tasks",
        headers=owner_b_headers,
        json={"title": "Task in workspace B"},
    )
    assert task_b_response.status_code == 201

    # Workspace B owner cannot list tasks from workspace A.
    list_response = client.get(
        f"/api/v1/projects/{project_a_id}/tasks",
        headers=owner_b_headers,
    )
    assert list_response.status_code == 404
    missing_project_response = client.get(
        f"/api/v1/projects/{project_a_id + 1000000}/tasks",
        headers=owner_b_headers,
    )
    assert missing_project_response.status_code == 404
    assert list_response.json() == missing_project_response.json()

    # Workspace B owner cannot update a task from workspace A.
    update_response = client.patch(
        f"/api/v1/tasks/{task_a_id}",
        headers=owner_b_headers,
        json={"title": "Unauthorized update"},
    )
    assert update_response.status_code == 404
    missing_task_update = client.patch(
        f"/api/v1/tasks/{task_a_id + 1000000}",
        headers=owner_b_headers,
        json={"title": "Missing task"},
    )
    assert missing_task_update.status_code == 404
    assert update_response.json() == missing_task_update.json()

    # Workspace B owner cannot delete a task from workspace A.
    delete_response = client.delete(
        f"/api/v1/tasks/{task_a_id}",
        headers=owner_b_headers,
    )
    assert delete_response.status_code == 404
    missing_task_delete = client.delete(
        f"/api/v1/tasks/{task_a_id + 1000000}",
        headers=owner_b_headers,
    )
    assert missing_task_delete.status_code == 404
    assert delete_response.json() == missing_task_delete.json()

    # The task in workspace A must remain unchanged.
    owner_a_response = client.get(
        f"/api/v1/projects/{project_a_id}/tasks",
        headers=owner_a_headers,
    )
    assert owner_a_response.status_code == 200
    assert owner_a_response.json()["total"] == 1
    assert owner_a_response.json()["items"][0]["title"] == ("Task in workspace A")

    # Workspace B owner can still access their own task.
    owner_b_response = client.get(
        f"/api/v1/projects/{project_b_id}/tasks",
        headers=owner_b_headers,
    )
    assert owner_b_response.status_code == 200
    assert owner_b_response.json()["total"] == 1
    assert owner_b_response.json()["items"][0]["title"] == ("Task in workspace B")
