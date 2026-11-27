"""Tests for task-assignment email scheduling and SMTP delivery."""

from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import Mock

import app.services.email as email_service
import app.services.task as task_service
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


def _enable_notifications(
    monkeypatch: pytest.MonkeyPatch,
    *,
    enabled: bool,
) -> None:
    monkeypatch.setattr(
        task_service,
        "get_settings",
        lambda: SimpleNamespace(EMAIL_NOTIFICATIONS_ENABLED=enabled),
    )


def test_assignment_emails_are_scheduled_only_for_new_assignees(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, owner_headers = register_and_login()
    first_assignee_id, _ = register_and_login()
    second_assignee_id, _ = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    add_workspace_member(owner_headers, workspace_id, first_assignee_id, "EDITOR")
    add_workspace_member(owner_headers, workspace_id, second_assignee_id, "EDITOR")
    _enable_notifications(monkeypatch, enabled=True)

    sent: list[dict[str, object]] = []

    commit_completed = False
    original_commit = AsyncSession.commit

    async def tracked_commit(session: AsyncSession) -> None:
        nonlocal commit_completed
        await original_commit(session)
        commit_completed = True

    def sender(**kwargs: object) -> None:
        nonlocal commit_completed
        assert commit_completed, "notification ran before the DB commit completed"
        commit_completed = False
        sent.append(kwargs)

    monkeypatch.setattr(AsyncSession, "commit", tracked_commit)
    monkeypatch.setattr(
        task_service,
        "send_task_assignment_email",
        sender,
    )

    tasks_url = f"/api/v1/projects/{project_id}/tasks"
    created = client.post(
        tasks_url,
        headers=owner_headers,
        json={"title": "Assigned task", "assignee_id": first_assignee_id},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert len(sent) == 1
    assert sent[0]["recipient_email"].endswith("@example.com")
    assert sent[0]["task_title"] == "Assigned task"
    assert sent[0]["project_name"] == "Task Test Project"

    commit_completed = False
    unrelated_update = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"title": "Renamed task"},
    )
    assert unrelated_update.status_code == 200
    assert len(sent) == 1

    commit_completed = False
    unchanged_assignee = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"assignee_id": first_assignee_id},
    )
    assert unchanged_assignee.status_code == 200
    assert len(sent) == 1

    commit_completed = False
    changed_assignee = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"assignee_id": second_assignee_id},
    )
    assert changed_assignee.status_code == 200
    assert len(sent) == 2

    commit_completed = False
    unassigned = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=owner_headers,
        json={"assignee_id": None},
    )
    assert unassigned.status_code == 200
    assert len(sent) == 2


def test_unassigned_task_does_not_schedule_email(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, headers = register_and_login()
    workspace_id = create_test_workspace(headers)
    project_id = create_test_project(headers, workspace_id)
    _enable_notifications(monkeypatch, enabled=True)
    sender = Mock()
    monkeypatch.setattr(task_service, "send_task_assignment_email", sender)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "No assignee"},
    )

    assert response.status_code == 201
    sender.assert_not_called()


def test_disabled_notifications_do_not_schedule_email(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, owner_headers = register_and_login()
    assignee_id, _ = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    add_workspace_member(owner_headers, workspace_id, assignee_id, "EDITOR")
    _enable_notifications(monkeypatch, enabled=False)
    sender = Mock()
    monkeypatch.setattr(task_service, "send_task_assignment_email", sender)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "Notifications off", "assignee_id": assignee_id},
    )

    assert response.status_code == 201
    sender.assert_not_called()


def test_smtp_sender_sends_assignment_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        EMAIL_NOTIFICATIONS_ENABLED=True,
        SMTP_HOST="smtp.example.test",
        SMTP_PORT=587,
        SMTP_SENDER_EMAIL="TaskHub <tasks@example.test>",
        SMTP_USE_SSL=False,
        SMTP_USE_STARTTLS=True,
        SMTP_USERNAME="mailer",
        SMTP_PASSWORD=SimpleNamespace(get_secret_value=lambda: "secret"),
    )
    monkeypatch.setattr(email_service, "get_settings", lambda: settings)
    smtp = Mock()
    smtp_context = Mock()
    smtp_context.__enter__ = Mock(return_value=smtp)
    smtp_context.__exit__ = Mock(return_value=False)
    smtp_factory = Mock(return_value=smtp_context)
    monkeypatch.setattr(email_service.smtplib, "SMTP", smtp_factory)

    email_service.send_task_assignment_email(
        "assignee@example.test",
        "Prepare release",
        "Mobile App",
        42,
    )

    smtp_factory.assert_called_once_with("smtp.example.test", 587, timeout=10)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("mailer", "secret")
    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["To"] == "assignee@example.test"
    assert "Prepare release" in sent_message.get_content()
    assert "Mobile App" in sent_message.get_content()
    assert "secret" not in sent_message.as_string()


def test_smtp_failure_is_swallowed_and_does_not_escape_background_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SimpleNamespace(
        EMAIL_NOTIFICATIONS_ENABLED=True,
        SMTP_HOST="smtp.example.test",
        SMTP_PORT=587,
        SMTP_SENDER_EMAIL="tasks@example.test",
        SMTP_USE_SSL=False,
        SMTP_USE_STARTTLS=False,
        SMTP_USERNAME=None,
        SMTP_PASSWORD=None,
    )
    monkeypatch.setattr(email_service, "get_settings", lambda: settings)
    monkeypatch.setattr(
        email_service.smtplib,
        "SMTP",
        Mock(side_effect=OSError("private SMTP diagnostic")),
    )

    # The sender catches delivery errors so a post-commit background task
    # cannot change the successful API response or roll back the DB operation.
    email_service.send_task_assignment_email(
        "assignee@example.test",
        "Prepare release",
        "Mobile App",
        42,
    )


def test_smtp_failure_does_not_fail_task_assignment_request(
    client: TestClient,
    register_and_login: Callable[[], tuple[int, dict[str, str]]],
    create_test_workspace: Callable[[dict[str, str]], int],
    create_test_project: Callable[[dict[str, str], int], int],
    add_workspace_member: Callable[[dict[str, str], int, int, str], None],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, owner_headers = register_and_login()
    assignee_id, _ = register_and_login()
    workspace_id = create_test_workspace(owner_headers)
    project_id = create_test_project(owner_headers, workspace_id)
    add_workspace_member(owner_headers, workspace_id, assignee_id, "EDITOR")
    _enable_notifications(monkeypatch, enabled=True)
    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(
            EMAIL_NOTIFICATIONS_ENABLED=True,
            SMTP_HOST="smtp.example.test",
            SMTP_PORT=587,
            SMTP_SENDER_EMAIL="tasks@example.test",
            SMTP_USE_SSL=False,
            SMTP_USE_STARTTLS=False,
            SMTP_USERNAME=None,
            SMTP_PASSWORD=None,
        ),
    )
    monkeypatch.setattr(
        email_service.smtplib,
        "SMTP",
        Mock(side_effect=OSError("private SMTP diagnostic")),
    )

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=owner_headers,
        json={"title": "SMTP unavailable", "assignee_id": assignee_id},
    )

    assert response.status_code == 201
    assert response.json()["assignee_id"] == assignee_id
