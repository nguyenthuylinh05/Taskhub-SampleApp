"""Comment management API tests."""

from collections.abc import Callable

import pytest
from app.core.constants import COMMENT_CONTENT_MAX_LENGTH
from app.core.messages import COMMENT_NOT_FOUND, PROJECT_ARCHIVED
from app.models.enums import WorkspaceRole
from app.schemas.comment import CommentCreate
from fastapi.testclient import TestClient
from pydantic import ValidationError


def test_create_list_and_delete_comments(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    user_id, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Comment test task")
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
    assert [item["id"] for item in listed.json()["items"]] == [comment_id]
    assert listed.json()["total"] == 1
    assert listed.json()["page"] == 1
    assert listed.json()["limit"] == 10

    deleted = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    empty = client.get(comments_url, headers=headers)
    assert empty.json()["items"] == []
    assert empty.json()["total"] == 0


def test_comment_content_and_protected_fields_validation(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    user_id, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Comment validation task")
    comments_url = f"/api/v1/tasks/{task_id}/comments"

    at_limit = client.post(
        comments_url,
        headers=headers,
        json={"content": "x" * COMMENT_CONTENT_MAX_LENGTH},
    )
    assert at_limit.status_code == 201

    over_limit = client.post(
        comments_url,
        headers=headers,
        json={"content": "x" * (COMMENT_CONTENT_MAX_LENGTH + 1)},
    )
    assert over_limit.status_code == 422

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
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    task_id = create_test_task(owner_headers, project_id, "Missing resource task")

    assert (
        client.post(
            "/api/v1/tasks/999999/comments",
            headers=owner_headers,
            json={"content": "Missing task"},
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/v1/tasks/999999/comments",
            headers=owner_headers,
        ).status_code
        == 404
    )
    missing_comment = client.delete(
        "/api/v1/comments/999999",
        headers=owner_headers,
    )
    assert missing_comment.status_code == 404
    assert missing_comment.json()["detail"] == COMMENT_NOT_FOUND
    assert (
        client.get(
            f"/api/v1/tasks/{task_id}/comments",
            headers=outsider_headers,
        ).status_code
        == 404
    )


def test_comment_writes_follow_workspace_roles(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
    set_workspace_member_role: Callable[[int, int, WorkspaceRole], None],
    promote_to_admin: Callable[[int], None],
) -> None:
    _, owner_headers = register_and_login()
    editor_id, editor_headers = register_and_login()
    viewer_id, viewer_headers = register_and_login()
    admin_id, admin_headers = register_and_login()
    _, outsider_headers = register_and_login()
    promote_to_admin(admin_id)
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    task_id = create_test_task(owner_headers, project_id, "Role policy task")
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

    owner_comment_response = client.post(
        comments_url,
        headers=owner_headers,
        json={"content": "Owner comment"},
    )
    assert owner_comment_response.status_code == 201
    owner_comment_id = owner_comment_response.json()["id"]
    assert client.get(comments_url, headers=viewer_headers).status_code == 200
    assert (
        client.post(
            comments_url,
            headers=viewer_headers,
            json={"content": "Viewer cannot comment"},
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/comments/{owner_comment_id}",
            headers=viewer_headers,
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/comments/{owner_comment_id}",
            headers=editor_headers,
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/comments/{owner_comment_id}",
            headers=outsider_headers,
        ).status_code
        == 404
    )

    editor_own_comment = client.post(
        comments_url,
        headers=editor_headers,
        json={"content": "Editor-owned comment"},
    )
    assert editor_own_comment.status_code == 201
    assert (
        client.delete(
            f"/api/v1/comments/{editor_own_comment.json()['id']}",
            headers=editor_headers,
        ).status_code
        == 204
    )

    owner_deletable_comment = client.post(
        comments_url,
        headers=editor_headers,
        json={"content": "Owner may delete"},
    )
    assert owner_deletable_comment.status_code == 201
    assert (
        client.delete(
            f"/api/v1/comments/{owner_deletable_comment.json()['id']}",
            headers=owner_headers,
        ).status_code
        == 204
    )

    viewer_owned_comment = client.post(
        comments_url,
        headers=editor_headers,
        json={"content": "Author is now a viewer"},
    )
    assert viewer_owned_comment.status_code == 201
    set_workspace_member_role(
        workspace_id,
        editor_id,
        WorkspaceRole.VIEWER,
    )
    assert (
        client.delete(
            f"/api/v1/comments/{viewer_owned_comment.json()['id']}",
            headers=editor_headers,
        ).status_code
        == 204
    )

    admin_deletable_comment = client.post(
        comments_url,
        headers=owner_headers,
        json={"content": "Admin may delete"},
    )
    assert admin_deletable_comment.status_code == 201
    admin_delete = client.delete(
        f"/api/v1/comments/{admin_deletable_comment.json()['id']}",
        headers=admin_headers,
    )
    assert admin_delete.status_code == 204


def test_comment_pagination(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Pagination task")
    comments_url = f"/api/v1/tasks/{task_id}/comments"

    for content in ("First", "Second", "Third"):
        response = client.post(
            comments_url,
            headers=headers,
            json={"content": content},
        )
        assert response.status_code == 201

    first_page = client.get(f"{comments_url}?page=1&limit=2", headers=headers)
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert first_page.json()["page"] == 1
    assert first_page.json()["limit"] == 2
    assert [item["content"] for item in first_page.json()["items"]] == [
        "First",
        "Second",
    ]

    second_page = client.get(f"{comments_url}?page=2&limit=2", headers=headers)
    assert second_page.status_code == 200
    assert second_page.json()["total"] == 3
    assert [item["content"] for item in second_page.json()["items"]] == ["Third"]

    empty_page = client.get(f"{comments_url}?page=3&limit=2", headers=headers)
    assert empty_page.status_code == 200
    assert empty_page.json()["items"] == []
    assert empty_page.json()["total"] == 3

    assert client.get(f"{comments_url}?limit=101", headers=headers).status_code == 422


def test_archived_project_rejects_comment_writes(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    _, headers = register_and_login()
    author_id, author_headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Archived comment task")
    add_workspace_member(headers, workspace_id, author_id, "EDITOR")
    comments_url = f"/api/v1/tasks/{task_id}/comments"
    existing = client.post(
        comments_url,
        headers=author_headers,
        json={"content": "Keep readable after archive"},
    )
    assert existing.status_code == 201
    comment_id = existing.json()["id"]

    archived = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archived.status_code == 200

    create_response = client.post(
        comments_url,
        headers=author_headers,
        json={"content": "Cannot create"},
    )
    author_delete_response = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers=author_headers,
    )
    owner_delete_response = client.delete(
        f"/api/v1/comments/{comment_id}",
        headers=headers,
    )
    assert create_response.status_code == 400
    assert create_response.json()["detail"] == PROJECT_ARCHIVED
    assert author_delete_response.status_code == 400
    assert author_delete_response.json()["detail"] == PROJECT_ARCHIVED
    assert owner_delete_response.status_code == 400
    assert owner_delete_response.json()["detail"] == PROJECT_ARCHIVED

    listed = client.get(comments_url, headers=author_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [comment_id]


def test_comment_schema_enforces_content_max_length() -> None:
    assert CommentCreate(content="x" * COMMENT_CONTENT_MAX_LENGTH)
    with pytest.raises(ValidationError):
        CommentCreate(content="x" * (COMMENT_CONTENT_MAX_LENGTH + 1))
