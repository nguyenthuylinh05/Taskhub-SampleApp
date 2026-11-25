"""Comment management API tests."""

from collections.abc import Callable

from fastapi.testclient import TestClient


def create_task(
    client: TestClient,
    headers: dict[str, str],
    project_id: int,
) -> int:
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Comment test task"},
    )
    assert response.status_code == 201
    task_id = response.json()["id"]
    assert isinstance(task_id, int)
    return task_id


def test_create_list_and_delete_comments(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    user_id, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_task(client, headers, project_id)
    comments_url = f"/api/v1/tasks/{task_id}/comments"

    created = client.post(
        comments_url,
        headers=headers,
        json={"content": "  First comment  "},
    )
    assert created.status_code == 201
    comment = created.json()
    comment_id = comment["id"]
    assert comment["task_id"] == task_id
    assert comment["author_id"] == user_id
    assert comment["content"] == "First comment"
    assert comment["created_at"]

    listed = client.get(comments_url, headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [comment_id]

    deleted = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert client.get(comments_url, headers=headers).json() == []


def test_comment_content_and_protected_fields_validation(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    user_id, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_task(client, headers, project_id)
    comments_url = f"/api/v1/tasks/{task_id}/comments"

    empty = client.post(comments_url, headers=headers, json={"content": ""})
    assert empty.status_code == 422
    whitespace = client.post(
        comments_url,
        headers=headers,
        json={"content": " \t  "},
    )
    assert whitespace.status_code == 422

    overridden = client.post(
        comments_url,
        headers=headers,
        json={
            "content": "Cannot override identity",
            "author_id": user_id + 100,
            "created_at": "2000-01-01T00:00:00Z",
        },
    )
    assert overridden.status_code == 422


def test_comments_reject_missing_and_inaccessible_resources(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    task_id = create_task(client, owner_headers, project_id)

    assert client.post(
        "/api/v1/tasks/999999/comments",
        headers=owner_headers,
        json={"content": "Missing task"},
    ).status_code == 404
    assert client.get(
        "/api/v1/tasks/999999/comments",
        headers=owner_headers,
    ).status_code == 404
    assert client.delete(
        "/api/v1/comments/999999",
        headers=owner_headers,
    ).status_code == 404
    assert client.get(
        f"/api/v1/tasks/{task_id}/comments",
        headers=outsider_headers,
    ).status_code == 404


def test_comment_writes_follow_workspace_roles(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
    promote_to_admin: Callable[[int], None],
) -> None:
    _, owner_headers = register_and_login()
    editor_id, editor_headers = register_and_login()
    viewer_id, viewer_headers = register_and_login()
    admin_id, admin_headers = register_and_login()
    promote_to_admin(admin_id)
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    task_id = create_task(client, owner_headers, project_id)
    add_workspace_member(
        owner_headers,
        workspace_id,
        editor_id,
        "EDITOR",
    )
    add_workspace_member(
        owner_headers,
        workspace_id,
        viewer_id,
        "VIEWER",
    )
    comments_url = f"/api/v1/tasks/{task_id}/comments"

    owner_comment = client.post(
        comments_url,
        headers=owner_headers,
        json={"content": "Owner comment"},
    ).json()
    assert client.get(comments_url, headers=viewer_headers).status_code == 200
    assert client.post(
        comments_url,
        headers=viewer_headers,
        json={"content": "Viewer cannot comment"},
    ).status_code == 403
    assert client.delete(
        f"/api/v1/comments/{owner_comment['id']}",
        headers=viewer_headers,
    ).status_code == 403

    # Editors may delete even when they did not author the comment, matching
    # existing Task deletion policy, which is role-based rather than ownership-based.
    assert client.delete(
        f"/api/v1/comments/{owner_comment['id']}",
        headers=editor_headers,
    ).status_code == 204

    admin_comment = client.post(
        comments_url,
        headers=admin_headers,
        json={"content": "Admin comment"},
    )
    assert admin_comment.status_code == 201
    assert client.delete(
        f"/api/v1/comments/{admin_comment.json()['id']}",
        headers=admin_headers,
    ).status_code == 204
