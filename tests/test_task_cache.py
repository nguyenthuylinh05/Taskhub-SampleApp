"""Task-list cache invalidation and transaction safety tests."""

from collections.abc import Callable

import pytest
import redis as redis_sync
from app.core.config import settings
from app.core.database import register_project_cache_invalidation
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
def get_project_cache_version(
    task_cache_redis: redis_sync.Redis,
) -> Callable[[int], str | None]:
    """Return a project cache version using the isolated Redis fixture."""

    def _get(project_id: int) -> str | None:
        version_key = f"task-list:project:{project_id}:version"
        version = task_cache_redis.get(version_key)
        if version is None:
            task_cache_redis.set(version_key, "1", nx=True)
            version = task_cache_redis.get(version_key)
        return str(version) if version is not None else "1"

    return _get


def test_task_mutations_increment_project_cache_version(
    client: TestClient,
    task_cache_redis: redis_sync.Redis,
    get_project_cache_version: Callable[[int], str | None],
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    assert get_project_cache_version(project_id) == "1"

    created = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Invalidate create"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    create_version = get_project_cache_version(project_id)
    assert create_version == "2"

    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Invalidate update",
            "status": "IN_PROGRESS",
            "priority": "HIGH",
        },
    )
    assert updated.status_code == 200
    assert get_project_cache_version(project_id) == "3"

    deleted = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert get_project_cache_version(project_id) == "4"

    version_key = f"task-list:project:{project_id}:version"
    assert task_cache_redis.ttl(version_key) == -1


def test_label_mutations_increment_project_cache_version(
    client: TestClient,
    get_project_cache_version: Callable[[int], str | None],
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    task = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Label cache task"},
    )
    assert task.status_code == 201
    task_id = task.json()["id"]

    label = client.post(
        f"/api/v1/projects/{project_id}/labels",
        headers=headers,
        json={"name": "Cache label", "color": "#123456"},
    )
    assert label.status_code == 201
    label_id = label.json()["id"]

    before_assignment = get_project_cache_version(project_id)
    assert (
        client.post(
            f"/api/v1/tasks/{task_id}/labels/{label_id}",
            headers=headers,
        ).status_code
        == 204
    )
    assert get_project_cache_version(project_id) != before_assignment

    before_removal = get_project_cache_version(project_id)
    assert (
        client.delete(
            f"/api/v1/tasks/{task_id}/labels/{label_id}",
            headers=headers,
        ).status_code
        == 204
    )
    assert get_project_cache_version(project_id) != before_removal

    updated = client.patch(
        f"/api/v1/labels/{label_id}",
        headers=headers,
        json={"name": "Updated label"},
    )
    assert updated.status_code == 200

    before_delete = get_project_cache_version(project_id)
    deleted = client.delete(
        f"/api/v1/labels/{label_id}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert get_project_cache_version(project_id) != before_delete


def test_multi_project_mutations_increment_every_project_version(
    client: TestClient,
    get_project_cache_version: Callable[[int], str | None],
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
) -> None:
    _, owner_headers = register_and_login()
    member_id, _ = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_a = create_test_project(owner_headers, workspace_id)
    project_b = create_test_project(owner_headers, workspace_id)
    add_workspace_member(owner_headers, workspace_id, member_id, "EDITOR")
    assert get_project_cache_version(project_a) == "1"
    assert get_project_cache_version(project_b) == "1"

    for project_id in (project_a, project_b):
        created = client.post(
            f"/api/v1/projects/{project_id}/tasks",
            headers=owner_headers,
            json={"title": f"Assigned task {project_id}", "assignee_id": member_id},
        )
        assert created.status_code == 201

    assert get_project_cache_version(project_a) == "2"
    assert get_project_cache_version(project_b) == "2"

    removed = client.delete(
        f"/api/v1/workspaces/{workspace_id}/members/{member_id}",
        headers=owner_headers,
    )
    assert removed.status_code == 204
    assert get_project_cache_version(project_a) != "2"
    assert get_project_cache_version(project_b) != "2"


def test_project_and_workspace_deletion_increment_versions(
    client: TestClient,
    get_project_cache_version: Callable[[int], str | None],
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_a = create_test_project(headers, workspace_id)
    project_b = create_test_project(headers, workspace_id)

    assert get_project_cache_version(project_a) == "1"
    assert get_project_cache_version(project_b) == "1"

    deleted_project = client.delete(
        f"/api/v1/workspaces/{workspace_id}/projects/{project_a}",
        headers=headers,
    )
    assert deleted_project.status_code == 204
    assert get_project_cache_version(project_a) == "2"
    assert get_project_cache_version(project_b) == "1"

    deleted_workspace = client.delete(
        f"/api/v1/workspaces/{workspace_id}",
        headers=headers,
    )
    assert deleted_workspace.status_code == 204
    assert get_project_cache_version(project_b) == "2"


@pytest.mark.asyncio
async def test_registered_invalidation_does_not_run_on_database_rollback(
    task_cache_redis: redis_sync.Redis,
) -> None:
    project_id = 998877
    assert task_cache_redis.get(f"task-list:project:{project_id}:version") in (
        None,
        "1",
    )

    engine = create_async_engine(settings.TEST_DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            register_project_cache_invalidation(session, project_id)
            await session.rollback()

        assert task_cache_redis.get(f"task-list:project:{project_id}:version") in (
            None,
            "1",
        )
    finally:
        await engine.dispose()


def test_redis_invalidation_failure_does_not_fail_mutation(
    client: TestClient,
    task_cache_redis: redis_sync.Redis,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)

    from unittest.mock import AsyncMock

    import app.core.redis as redis_module

    monkeypatch.setattr(
        redis_module.redis_client,
        "incr",
        AsyncMock(side_effect=TimeoutError("Redis invalidation timeout")),
    )

    created = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Redis failure remains successful"},
    )
    assert created.status_code == 201
