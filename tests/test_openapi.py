"""Contract checks for the generated API documentation."""

from app.main import app


def test_swagger_redoc_and_openapi_routes_are_registered() -> None:
    route_paths = {getattr(route, "path", None) for route in app.routes}

    assert "/docs" in route_paths
    assert "/redoc" in route_paths
    assert "/openapi.json" in route_paths


def test_openapi_metadata_and_bearer_security() -> None:
    schema = app.openapi()

    assert schema["info"]["title"] == "TaskHub — Task Management API"
    assert schema["info"]["version"]
    assert "workspaces" in schema["info"]["description"]

    bearer = schema["components"]["securitySchemes"]["BearerAuth"]
    assert bearer["type"] == "http"
    assert bearer["scheme"] == "bearer"
    assert bearer["bearerFormat"] == "JWT"

    task_list = schema["paths"]["/api/v1/projects/{project_id}/tasks"]["get"]
    assert {"BearerAuth": []} in task_list["security"]


def test_task_and_auth_operations_document_behavior_and_errors() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    create_task = paths["/api/v1/projects/{project_id}/tasks"]["post"]
    update_task = paths["/api/v1/tasks/{task_id}"]["patch"]
    login = paths["/api/v1/auth/login"]["post"]

    assert "assignment email" in create_task["description"]
    assert "different workspace member" in update_task["description"]
    assert "201" in create_task["responses"]
    assert "400" in create_task["responses"]
    assert "401" in create_task["responses"]
    assert "403" in create_task["responses"]
    assert "404" in create_task["responses"]
    assert "422" in create_task["responses"]
    assert "500" in create_task["responses"]
    assert "401" in login["responses"]
    assert login["summary"] == "Log in"


def test_comment_delete_documentation_matches_current_permissions() -> None:
    operation = app.openapi()["paths"]["/api/v1/comments/{comment_id}"]["delete"]

    assert "workspace OWNER" in operation["description"]
    assert "system ADMIN" in operation["description"]
    assert "cannot delete another user's comment" in operation["description"]
