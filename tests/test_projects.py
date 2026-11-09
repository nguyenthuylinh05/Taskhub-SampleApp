from collections.abc import Generator

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_project(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Website Project",
            "description": "Build company website",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Website Project"
    assert data["description"] == "Build company website"
    assert "id" in data
    assert "created_at" in data


def test_get_projects(client: TestClient) -> None:
    client.post(
        "/api/v1/projects",
        json={"name": "Project A"},
    )

    response = client.get("/api/v1/projects")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_project(client: TestClient) -> None:
    created = client.post(
        "/api/v1/projects",
        json={"name": "Old Name"},
    )

    project_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_project(client: TestClient) -> None:
    created = client.post(
        "/api/v1/projects",
        json={"name": "Delete Me"},
    )

    project_id = created.json()["id"]

    response = client.delete(f"/api/v1/projects/{project_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/projects/{project_id}")

    assert get_response.status_code == 404


def test_create_project_validation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects",
        json={"name": ""},
    )

    assert response.status_code == 422


def test_get_nonexistent_project(client: TestClient) -> None:
    from uuid import uuid4

    response = client.get(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404
