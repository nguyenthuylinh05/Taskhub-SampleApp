from typing import TypedDict, cast
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import jwt
from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from fastapi.testclient import TestClient


class RegisteredUser(TypedDict):
    id: int
    email: str
    full_name: str


def register_user(
    client: TestClient,
    cleanup_user: list[int],
) -> RegisteredUser:
    """Register a unique test user."""

    email = f"test_{uuid4().hex[:12]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    user_data = response.json()
    cleanup_user.append(user_data["id"])

    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "full_name": user_data["full_name"],
    }


def login_user(
    client: TestClient,
    user_data: RegisteredUser,
) -> str:
    """Login a test user and return the access token."""

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    return cast(str, response.json()["access_token"])


def test_register_success(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"register_{uuid4().hex[:12]}@example.com",
            "full_name": "New User",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 201

    user_data = response.json()
    assert user_data["email"].startswith("register_")
    assert user_data["full_name"] == "New User"
    assert "hashed_password" not in user_data

    cleanup_user.append(user_data["id"])


def test_register_duplicate_email(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_data["email"],
            "full_name": "Duplicate User",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 409


def test_login_success(
    client: TestClient,
    cleanup_user: list[int],
    mock_redis: dict[str, AsyncMock],
) -> None:
    user_data = register_user(client, cleanup_user)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 200

    token_data = response.json()
    assert token_data["access_token"]
    assert token_data["refresh_token"]
    assert token_data["token_type"] == "bearer"

    mock_redis["store"].assert_awaited_once()

    assert mock_redis["store"].await_args is not None
    stored_kwargs = mock_redis["store"].await_args.kwargs
    assert stored_kwargs["user_id"] == str(user_data["id"])
    assert stored_kwargs["jti"]
    assert stored_kwargs["expire_seconds"] == 7 * 24 * 60 * 60


def test_login_invalid_password(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 401


def test_refresh_token_success(
    client: TestClient,
    cleanup_user: list[int],
    mock_redis: dict[str, AsyncMock],
) -> None:
    user_data = register_user(client, cleanup_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    old_refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert response.status_code == 200

    token_data = response.json()
    assert token_data["access_token"]
    assert token_data["refresh_token"]
    assert token_data["refresh_token"] != old_refresh_token

    mock_redis["rotate"].assert_awaited_once()

    assert mock_redis["rotate"].await_args is not None
    rotate_kwargs = mock_redis["rotate"].await_args.kwargs
    assert rotate_kwargs["user_id"] == str(user_data["id"])
    assert rotate_kwargs["old_jti"]
    assert rotate_kwargs["new_jti"]
    assert rotate_kwargs["old_jti"] != rotate_kwargs["new_jti"]


def test_refresh_revoked_token(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    with patch(
        "app.services.auth.rotate_refresh_token",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock_rotate:
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 401
    mock_rotate.assert_awaited_once()


def test_logout_success(
    client: TestClient,
    cleanup_user: list[int],
    mock_redis: dict[str, AsyncMock],
) -> None:
    user_data = register_user(client, cleanup_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 204

    mock_redis["revoke"].assert_awaited_once()

    assert mock_redis["revoke"].await_args is not None
    revoke_kwargs = mock_redis["revoke"].await_args.kwargs
    assert revoke_kwargs["user_id"] == str(user_data["id"])
    assert revoke_kwargs["jti"]
    assert revoke_kwargs["expire_seconds"] == 7 * 24 * 60 * 60


def test_logout_revoked_token(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    with patch(
        "app.services.auth.revoke_refresh_token",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock_revoke:
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 401
    mock_revoke.assert_awaited_once()


def test_get_current_user(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)
    access_token = login_user(client, user_data)

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    profile = response.json()
    assert profile["id"] == user_data["id"]
    assert profile["email"] == user_data["email"]
    assert profile["full_name"] == user_data["full_name"]
    assert "hashed_password" not in profile


def test_get_current_user_without_token(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code in (401, 403)


def test_update_current_user_profile(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)
    access_token = login_user(client, user_data)

    response = client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"full_name": "Updated Test User"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Test User"
    assert response.json()["email"] == user_data["email"]


def test_change_password_success(
    client: TestClient,
    cleanup_user: list[int],
    mock_redis: dict[str, AsyncMock],
) -> None:
    user_data = register_user(client, cleanup_user)
    access_token = login_user(client, user_data)

    response = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "TestPassword123",
            "new_password": "NewPassword123",
        },
    )

    assert response.status_code == 204

    mock_redis["revoke_all"].assert_awaited_once_with(str(user_data["id"]))

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "NewPassword123",
        },
    )

    assert login_response.status_code == 200


def test_change_password_wrong_current_password(
    client: TestClient,
    cleanup_user: list[int],
    mock_redis: dict[str, AsyncMock],
) -> None:
    user_data = register_user(client, cleanup_user)
    access_token = login_user(client, user_data)

    response = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "WrongPassword123",
            "new_password": "NewPassword123",
        },
    )

    assert response.status_code == 400
    mock_redis["revoke_all"].assert_not_awaited()


def test_refresh_token_cannot_access_protected_endpoint(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401


def test_access_token_missing_required_claims(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)

    invalid_token = jwt.encode(
        {
            "sub": str(user_data["id"]),
            "type": "access",
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_access_protected_endpoint(
    client: TestClient,
    cleanup_user: list[int],
) -> None:
    user_data = register_user(client, cleanup_user)
    access_token = login_user(client, user_data)

    response = client.patch(
        f"/api/v1/users/{user_data['id']}",
        json={"is_active": False},
    )

    assert response.status_code in (200, 204)

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user"
