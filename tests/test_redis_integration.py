from uuid import uuid4

import pytest
from app.core.redis import (
    redis_client,
    rotate_refresh_token,
    store_refresh_token,
)


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection_with_real_redis() -> None:
    """Verify rotation and reuse detection against a real Redis server."""

    user_id = f"redis-integration-{uuid4().hex}"

    old_jti = uuid4().hex
    active_jti = uuid4().hex
    rotated_jti = uuid4().hex
    attempted_jti = uuid4().hex

    expire_seconds = 300

    refresh_keys = [
        f"refresh_token:{jti}"
        for jti in (
            old_jti,
            active_jti,
            rotated_jti,
            attempted_jti,
        )
    ]

    revoked_keys = [
        f"revoked_refresh_token:{jti}"
        for jti in (
            old_jti,
            active_jti,
            rotated_jti,
            attempted_jti,
        )
    ]

    sessions_key = f"user_refresh_tokens:{user_id}"

    try:
        # Ensure this test is connected to a real Redis server.
        assert await redis_client.ping()

        # Arrange: create two active refresh-token sessions.
        await store_refresh_token(
            jti=old_jti,
            user_id=user_id,
            expire_seconds=expire_seconds,
        )

        await store_refresh_token(
            jti=active_jti,
            user_id=user_id,
            expire_seconds=expire_seconds,
        )

        # Act 1: rotate the first refresh token.
        rotated = await rotate_refresh_token(
            old_jti=old_jti,
            new_jti=rotated_jti,
            user_id=user_id,
            expire_seconds=expire_seconds,
        )

        # Assert 1: the old token is revoked and the new one is active.
        assert rotated is True
        assert await redis_client.get(f"refresh_token:{old_jti}") is None
        assert await redis_client.get(f"refresh_token:{rotated_jti}") == user_id
        assert await redis_client.get(f"revoked_refresh_token:{old_jti}") == user_id

        assert (
            await redis_client.sismember(
                sessions_key,
                old_jti,
            )
            == 0
        )
        assert (
            await redis_client.sismember(
                sessions_key,
                rotated_jti,
            )
            == 1
        )

        # Act 2: attempt to reuse the already rotated old token.
        reused = await rotate_refresh_token(
            old_jti=old_jti,
            new_jti=attempted_jti,
            user_id=user_id,
            expire_seconds=expire_seconds,
        )

        # Assert 2: reuse is rejected and all active sessions are revoked.
        assert reused is False

        assert await redis_client.get(f"refresh_token:{rotated_jti}") is None
        assert await redis_client.get(f"refresh_token:{active_jti}") is None
        assert await redis_client.get(f"refresh_token:{attempted_jti}") is None

        assert await redis_client.get(f"revoked_refresh_token:{old_jti}") == user_id
        assert await redis_client.get(f"revoked_refresh_token:{rotated_jti}") == user_id
        assert await redis_client.get(f"revoked_refresh_token:{active_jti}") == user_id

        assert await redis_client.exists(sessions_key) == 0

    finally:
        # Clean up only keys created by this test.
        await redis_client.delete(
            *refresh_keys,
            *revoked_keys,
            sessions_key,
        )
