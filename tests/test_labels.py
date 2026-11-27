"""Label management API tests."""

from collections.abc import Callable

import asyncpg
import pytest
from app.core.constants import (
    LABEL_NAME_MAX_LENGTH,
    LABEL_PROJECT_NAME_CONSTRAINT,
)
from app.core.exceptions import ConflictError
from app.core.messages import (
    LABEL_NAME_ALREADY_EXISTS,
    LABEL_NOT_ASSIGNED,
    LABEL_NOT_FOUND,
    PROJECT_ARCHIVED,
    UPDATE_FIELDS_REQUIRED,
)
from app.schemas.label import LabelCreate, LabelUpdate
from app.services.label import _raise_label_name_conflict
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_dbapi
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


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


def test_label_crud_and_task_association(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_project(client, headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Label test task")
    other_task_id = create_test_task(headers, project_id, "Other label task")
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
    assert [item["id"] for item in listed.json()["items"]] == [label_id]
    assert listed.json()["total"] == 1
    assert listed.json()["page"] == 1
    assert listed.json()["limit"] == 10

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

    other_assignment_url = f"/api/v1/tasks/{other_task_id}/labels/{label_id}"
    assert client.post(other_assignment_url, headers=headers).status_code == 204

    removed = client.delete(assignment_url, headers=headers)
    assert removed.status_code == 204
    second_remove = client.delete(assignment_url, headers=headers)
    assert second_remove.status_code == 404
    assert second_remove.json()["detail"] == LABEL_NOT_ASSIGNED
    assert client.delete(other_assignment_url, headers=headers).status_code == 204

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
    missing_label = client.get("/api/v1/labels/999999", headers=headers)
    assert missing_label.status_code == 404
    assert missing_label.json()["detail"] == LABEL_NOT_FOUND
    assert (
        client.patch(
            "/api/v1/labels/999999",
            headers=headers,
            json={"name": "Missing"},
        ).status_code
        == 404
    )
    assert client.delete("/api/v1/labels/999999", headers=headers).status_code == 404
    assert (
        client.post(
            "/api/v1/tasks/999999/labels/1",
            headers=headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            "/api/v1/tasks/999999/labels/1",
            headers=headers,
        ).status_code
        == 404
    )


def test_labels_cannot_cross_projects_or_workspace_access(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, owner_headers = register_and_login()
    _, outsider_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_one = create_project(client, owner_headers, workspace_id)
    project_two = create_project(client, owner_headers, workspace_id, "Other")
    task_id = create_test_task(owner_headers, project_one, "Cross project task")
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
    assert cross_project.status_code == 404
    assert cross_project.json()["detail"] == LABEL_NOT_FOUND
    hidden_label = client.get(
        f"/api/v1/labels/{label.json()['id']}",
        headers=outsider_headers,
    )
    assert hidden_label.status_code == 404
    assert hidden_label.json()["detail"] == LABEL_NOT_FOUND

    hidden = client.get(
        f"/api/v1/projects/{project_one}/labels",
        headers=outsider_headers,
    )
    assert hidden.status_code == 404


def test_viewer_is_read_only_for_labels(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, owner_headers = register_and_login()
    viewer_id, viewer_headers = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_project(client, owner_headers, workspace_id)
    task_id = create_test_task(owner_headers, project_id, "Viewer label task")
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

    assert (
        client.get(
            f"/api/v1/projects/{project_id}/labels",
            headers=viewer_headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/projects/{project_id}/labels",
            headers=viewer_headers,
            json={"name": "Denied", "color": "#112233"},
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/labels/{label['id']}",
            headers=viewer_headers,
            json={"name": "Denied"},
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/v1/labels/{label['id']}",
            headers=viewer_headers,
        ).status_code
        == 403
    )
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
    assert (
        client.patch(
            f"/api/v1/labels/{created.json()['id']}",
            headers=editor_headers,
            json={"name": "Updated by editor"},
        ).status_code
        == 200
    )


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
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/labels",
            headers=admin_headers,
        ).status_code
        == 200
    )


def test_label_names_are_unique_per_project(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_one = create_project(client, headers, workspace_id, "First")
    project_two = create_project(client, headers, workspace_id, "Second")
    label_data = {"name": "Shared", "color": "#112233"}

    created = client.post(
        f"/api/v1/projects/{project_one}/labels",
        headers=headers,
        json=label_data,
    )
    assert created.status_code == 201

    duplicate = client.post(
        f"/api/v1/projects/{project_one}/labels",
        headers=headers,
        json=label_data,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == LABEL_NAME_ALREADY_EXISTS

    other_project = client.post(
        f"/api/v1/projects/{project_two}/labels",
        headers=headers,
        json=label_data,
    )
    assert other_project.status_code == 201

    another_label = client.post(
        f"/api/v1/projects/{project_one}/labels",
        headers=headers,
        json={"name": "Different", "color": "#112233"},
    )
    assert another_label.status_code == 201
    renamed_duplicate = client.patch(
        f"/api/v1/labels/{another_label.json()['id']}",
        headers=headers,
        json={"name": "Shared"},
    )
    assert renamed_duplicate.status_code == 409
    assert renamed_duplicate.json()["detail"] == LABEL_NAME_ALREADY_EXISTS


def test_labels_from_another_workspace_are_hidden(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, first_owner_headers = register_and_login()
    _, second_owner_headers = register_and_login()
    first_workspace = create_test_workspace(first_owner_headers)
    second_workspace = create_test_workspace(second_owner_headers)
    first_project = create_project(client, first_owner_headers, first_workspace)
    second_project = create_project(client, second_owner_headers, second_workspace)
    task_id = create_test_task(first_owner_headers, first_project, "Private task")
    label = client.post(
        f"/api/v1/projects/{second_project}/labels",
        headers=second_owner_headers,
        json={"name": "Private label", "color": "#112233"},
    )
    assert label.status_code == 201

    label_id = label.json()["id"]
    hidden = client.get(
        f"/api/v1/labels/{label_id}",
        headers=first_owner_headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == LABEL_NOT_FOUND

    assignment = client.post(
        f"/api/v1/tasks/{task_id}/labels/{label_id}",
        headers=first_owner_headers,
    )
    assert assignment.status_code == 404
    assert assignment.json()["detail"] == LABEL_NOT_FOUND


def test_label_pagination(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_project(client, headers, workspace_id)
    labels_url = f"/api/v1/projects/{project_id}/labels"

    for name in ("First", "Second", "Third"):
        response = client.post(
            labels_url,
            headers=headers,
            json={"name": name, "color": "#112233"},
        )
        assert response.status_code == 201

    first_page = client.get(f"{labels_url}?page=1&limit=2", headers=headers)
    assert first_page.status_code == 200
    assert first_page.json()["total"] == 3
    assert first_page.json()["page"] == 1
    assert first_page.json()["limit"] == 2
    assert len(first_page.json()["items"]) == 2

    second_page = client.get(f"{labels_url}?page=2&limit=2", headers=headers)
    assert second_page.status_code == 200
    assert second_page.json()["total"] == 3
    assert len(second_page.json()["items"]) == 1

    empty_page = client.get(f"{labels_url}?page=3&limit=2", headers=headers)
    assert empty_page.status_code == 200
    assert empty_page.json()["items"] == []
    assert empty_page.json()["total"] == 3

    assert client.get(f"{labels_url}?limit=101", headers=headers).status_code == 422


def test_archived_project_rejects_label_writes(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_task: Callable[[dict[str, str], int, str], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_project(client, headers, workspace_id)
    task_id = create_test_task(headers, project_id, "Archived project task")
    label = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=headers,
        json={"name": "Existing", "color": "#112233"},
    )
    unassigned_label = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=headers,
        json={"name": "Unassigned", "color": "#445566"},
    )
    assert label.status_code == 201
    assert unassigned_label.status_code == 201
    association = f"/api/v1/tasks/{task_id}/labels/{label.json()['id']}"
    assert client.post(association, headers=headers).status_code == 204

    archived = client.patch(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_id}",
        headers=headers,
        json={"status": "ARCHIVED"},
    )
    assert archived.status_code == 200

    rejected = (
        client.post(
            f"/api/v1/projects/{project_id}/labels",
            headers=headers,
            json={"name": "New", "color": "#112233"},
        ),
        client.patch(
            f"/api/v1/labels/{label.json()['id']}",
            headers=headers,
            json={"name": "Changed"},
        ),
        client.delete(f"/api/v1/labels/{label.json()['id']}", headers=headers),
        client.post(
            f"/api/v1/tasks/{task_id}/labels/{unassigned_label.json()['id']}",
            headers=headers,
        ),
        client.delete(association, headers=headers),
    )
    assert all(response.status_code == 400 for response in rejected)
    assert all(response.json()["detail"] == PROJECT_ARCHIVED for response in rejected)
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/labels",
            headers=headers,
        ).status_code
        == 200
    )


def test_label_schema_uses_limits_and_shared_update_message() -> None:
    assert LabelCreate(name="x", color="#aBc123")
    assert LabelCreate(name="x" * LABEL_NAME_MAX_LENGTH, color="#aBc123")
    with pytest.raises(ValidationError):
        LabelCreate(name="x" * (LABEL_NAME_MAX_LENGTH + 1), color="#aBc123")
    with pytest.raises(ValidationError, match=UPDATE_FIELDS_REQUIRED):
        LabelUpdate()


def _wrap_asyncpg_error(driver_error: Exception | None) -> IntegrityError:
    """Build the same DBAPI and SQLAlchemy wrappers used by asyncpg."""

    dbapi = AsyncAdapt_asyncpg_dbapi(asyncpg)
    if driver_error is None:
        adapted_error = dbapi.IntegrityError("synthetic integrity error")
    else:
        adapted_error_type = dbapi._asyncpg_error_translate[type(driver_error)]
        adapted_error = adapted_error_type(str(driver_error), driver_error)

    return IntegrityError("INSERT INTO labels", {}, adapted_error)


def test_label_unique_violation_becomes_conflict() -> None:
    driver_error = asyncpg.exceptions.UniqueViolationError("duplicate label")
    driver_error.constraint_name = LABEL_PROJECT_NAME_CONSTRAINT
    error = _wrap_asyncpg_error(driver_error)

    assert error.orig.sqlstate == "23505"
    assert error.orig.orig is driver_error
    assert error.orig.orig.constraint_name == LABEL_PROJECT_NAME_CONSTRAINT

    with pytest.raises(ConflictError) as conflict:
        _raise_label_name_conflict(error)

    assert conflict.value.message == LABEL_NAME_ALREADY_EXISTS
    assert conflict.value.status_code == 409


def test_other_unique_constraint_is_not_label_name_conflict() -> None:
    driver_error = asyncpg.exceptions.UniqueViolationError("other duplicate")
    driver_error.constraint_name = "uq_other_resource"
    error = _wrap_asyncpg_error(driver_error)

    assert error.orig.sqlstate == "23505"
    assert error.orig.orig.constraint_name == "uq_other_resource"
    with pytest.raises(IntegrityError) as raised:
        _raise_label_name_conflict(error)
    assert raised.value is error


def test_foreign_key_violation_is_not_label_name_conflict() -> None:
    driver_error = asyncpg.exceptions.ForeignKeyViolationError("missing parent")
    driver_error.constraint_name = "fk_labels_project_id_projects"
    error = _wrap_asyncpg_error(driver_error)

    assert error.orig.sqlstate == "23503"
    assert error.orig.orig.constraint_name == "fk_labels_project_id_projects"
    with pytest.raises(IntegrityError) as raised:
        _raise_label_name_conflict(error)
    assert raised.value is error


def test_integrity_error_without_metadata_is_preserved() -> None:
    error = _wrap_asyncpg_error(None)

    assert error.orig.sqlstate is None
    assert error.orig.orig is None
    with pytest.raises(IntegrityError) as raised:
        _raise_label_name_conflict(error)
    assert raised.value is error


@pytest.mark.asyncio
async def test_label_name_constraint_is_migrated(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()
    constraints = await connection.run_sync(
        lambda sync_connection: inspect(sync_connection).get_unique_constraints(
            "labels"
        )
    )

    assert any(
        constraint["name"] == LABEL_PROJECT_NAME_CONSTRAINT
        and constraint["column_names"] == ["project_id", "name"]
        for constraint in constraints
    )
