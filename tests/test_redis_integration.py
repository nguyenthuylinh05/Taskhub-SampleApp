"""Integration tests for Redis refresh-token operations."""

from uuid import uuid4

import app.core.redis as redis_module
import pytest
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection_with_real_redis(
    real_redis: Redis,
) -> None:
    """Verify rotation and reuse detection against a real Redis server."""

    user_id = f"redis-integration-{uuid4().hex}"

    old_jti = uuid4().hex
    active_jti = uuid4().hex
    rotated_jti = uuid4().hex
    attempted_jti = uuid4().hex

    expire_seconds = 300

    refresh_keys = [
        f"refresh_token:{jti}"
        for jti in (old_jti, active_jti, rotated_jti, attempted_jti)
    ]

    revoked_keys = [
        f"revoked_refresh_token:{jti}"
        for jti in (old_jti, active_jti, rotated_jti, attempted_jti)
    ]

    sessions_key = f"user_refresh_tokens:{user_id}"

    try:
        assert await real_redis.ping()

        # Arrange: create two active sessions.
        await redis_module.store_refresh_token(
            old_jti,
            user_id,
            expire_seconds,
        )
        await redis_module.store_refresh_token(
            active_jti,
            user_id,
            expire_seconds,
        )

        # Act 1: rotate the first token.
        rotated = await redis_module.rotate_refresh_token(
            old_jti,
            rotated_jti,
            user_id,
            expire_seconds,
        )

        # Assert 1: old token is revoked and new token is active.
        assert rotated is True
        assert await real_redis.get(f"refresh_token:{old_jti}") is None
        assert await real_redis.get(f"refresh_token:{rotated_jti}") == user_id
        assert (
            await real_redis.get(f"revoked_refresh_token:{old_jti}")
            == user_id
        )

        assert await real_redis.sismember(sessions_key, old_jti) == 0
        assert await real_redis.sismember(sessions_key, rotated_jti) == 1

        # Act 2: attempt to reuse the old token.
        reused = await redis_module.rotate_refresh_token(
            old_jti,
            attempted_jti,
            user_id,
            expire_seconds,
        )

        # Assert 2: reuse is rejected and all sessions are revoked.
        assert reused is False

        assert await real_redis.get(f"refresh_token:{rotated_jti}") is None
        assert await real_redis.get(f"refresh_token:{active_jti}") is None
        assert await real_redis.get(f"refresh_token:{attempted_jti}") is None

        assert (
            await real_redis.get(f"revoked_refresh_token:{old_jti}")
            == user_id
        )
        assert (
            await real_redis.get(f"revoked_refresh_token:{rotated_jti}")
            == user_id
        )
        assert (
            await real_redis.get(f"revoked_refresh_token:{active_jti}")
            == user_id
        )

        assert await real_redis.exists(sessions_key) == 0

    finally:
        await real_redis.delete(
            *refresh_keys,
            *revoked_keys,
            sessions_key,
        )


@pytest.mark.asyncio
async def test_revoke_refresh_token_with_real_redis(
    real_redis: Redis,
) -> None:
    """Verify that one refresh token can be revoked."""

    user_id = f"redis-integration-{uuid4().hex}"
    jti = uuid4().hex
    other_jti = uuid4().hex

    expire_seconds = 300

    refresh_keys = [
        f"refresh_token:{jti}",
        f"refresh_token:{other_jti}",
    ]
    revoked_key = f"revoked_refresh_token:{jti}"
    sessions_key = f"user_refresh_tokens:{user_id}"

    try:
        assert await real_redis.ping()

        # Arrange: create two active sessions.
        await redis_module.store_refresh_token(
            jti,
            user_id,
            expire_seconds,
        )
        await redis_module.store_refresh_token(
            other_jti,
            user_id,
            expire_seconds,
        )

        # Act: revoke one token.
        revoked = await redis_module.revoke_refresh_token(
            jti,
            user_id,
            expire_seconds,
        )

        # Assert: only the selected token is revoked.
        assert revoked is True
        assert await real_redis.get(f"refresh_token:{jti}") is None
        assert await real_redis.get(revoked_key) == user_id

        assert await real_redis.get(f"refresh_token:{other_jti}") == user_id

        assert await real_redis.sismember(sessions_key, jti) == 0
        assert await real_redis.sismember(sessions_key, other_jti) == 1

        # Act 2: try revoking the same token again.
        revoked_again = await redis_module.revoke_refresh_token(
            jti,
            user_id,
            expire_seconds,
        )

        # Assert: the already revoked token cannot be revoked again.
        assert revoked_again is False

    finally:
        await real_redis.delete(
            *refresh_keys,
            revoked_key,
            sessions_key,
        )


@pytest.mark.asyncio
async def test_revoke_all_refresh_tokens_with_real_redis(
    real_redis: Redis,
) -> None:
    """Verify that all refresh tokens belonging to a user are revoked."""

    user_id = f"redis-integration-{uuid4().hex}"

    jtis = [uuid4().hex for _ in range(3)]
    expire_seconds = 300

    refresh_keys = [f"refresh_token:{jti}" for jti in jtis]
    revoked_keys = [f"revoked_refresh_token:{jti}" for jti in jtis]
    sessions_key = f"user_refresh_tokens:{user_id}"

    try:
        assert await real_redis.ping()

        # Arrange: create three active sessions.
        for jti in jtis:
            await redis_module.store_refresh_token(
                jti,
                user_id,
                expire_seconds,
            )

        assert await real_redis.scard(sessions_key) == 3

        # Act: revoke all refresh tokens.
        revoked_count = await redis_module.revoke_all_refresh_tokens(
            user_id,
        )

        # Assert: all three tokens are revoked.
        assert revoked_count == 3

        for jti in jtis:
            assert await real_redis.get(f"refresh_token:{jti}") is None
            assert (
                await real_redis.get(f"revoked_refresh_token:{jti}")
                == user_id
            )

        assert await real_redis.exists(sessions_key) == 0

        # Act 2: revoke all again when no sessions remain.
        revoked_again = await redis_module.revoke_all_refresh_tokens(
            user_id,
        )

        # Assert: no additional tokens are revoked.
        assert revoked_again == 0

    finally:
        await real_redis.delete(
            *refresh_keys,
            *revoked_keys,
            sessions_key,
        )