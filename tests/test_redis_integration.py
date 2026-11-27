"""Integration tests for Redis refresh-token operations."""

from uuid import uuid4

import app.core.redis as redis_module
import pytest
from app.core.config import REDIS_TASK_CACHE_TTL_SECONDS
from app.core.redis import (
    get_task_list_cache_version,
    get_task_list_cached_response,
    increment_task_list_cache_version,
    set_task_list_cached_response,
    task_list_cache_key,
    task_list_query_hash,
)
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
        assert await real_redis.get(f"revoked_refresh_token:{old_jti}") == user_id

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

        assert await real_redis.get(f"revoked_refresh_token:{old_jti}") == user_id
        assert await real_redis.get(f"revoked_refresh_token:{rotated_jti}") == user_id
        assert await real_redis.get(f"revoked_refresh_token:{active_jti}") == user_id

        assert await real_redis.exists(sessions_key) == 0

    finally:
        await real_redis.delete(
            *refresh_keys,
            *revoked_keys,
            sessions_key,
        )


@pytest.mark.asyncio
async def test_task_list_cache_set_get_and_ttl(real_redis: Redis) -> None:
    project_id = 987654
    user_id = 123456
    cache_key = task_list_cache_key(project_id, user_id, "1", "cache-test")

    try:
        assert await real_redis.ping()
        await set_task_list_cached_response(
            cache_key,
            '{"items":[],"total":0,"page":1,"limit":10}',
            30,
        )
        assert (
            await get_task_list_cached_response(cache_key)
            == '{"items":[],"total":0,"page":1,"limit":10}'
        )
        assert await real_redis.ttl(cache_key) > 0
        assert REDIS_TASK_CACHE_TTL_SECONDS >= 1
    finally:
        await real_redis.delete(cache_key)


@pytest.mark.asyncio
async def test_task_list_cache_keys_distinguish_and_version(real_redis: Redis) -> None:
    project_id = 987655
    version_key = f"task-list:project:{project_id}:version"

    try:
        await real_redis.delete(version_key)
        assert await get_task_list_cache_version(project_id) == "1"

        await increment_task_list_cache_version(project_id)
        assert await get_task_list_cache_version(project_id) == "2"

        assert task_list_cache_key(project_id, 10, "2", "alpha") != task_list_cache_key(
            project_id, 11, "2", "alpha"
        )
        assert task_list_cache_key(project_id, 10, "2", "alpha") != task_list_cache_key(
            project_id, 10, "2", "beta"
        )
        assert task_list_cache_key(project_id, 10, "2", "alpha") != task_list_cache_key(
            987656, 10, "2", "alpha"
        )
    finally:
        await real_redis.delete(version_key)


def test_task_list_query_hash_canonicalizes_equivalent_queries() -> None:
    alpha_hash = task_list_query_hash(
        status=["TODO", "IN_PROGRESS", "TODO"],
        priority=["HIGH", "LOW", "HIGH"],
        assignee_id=42,
        page=2,
        limit=20,
        search="  Alpha  ",
    )
    lowercase_hash = task_list_query_hash(
        status=["IN_PROGRESS", "TODO"],
        priority=["LOW", "HIGH"],
        assignee_id=42,
        page=2,
        limit=20,
        search="alpha",
    )

    assert alpha_hash == lowercase_hash


def test_task_list_query_hash_separates_semantically_different_queries() -> None:
    base = task_list_query_hash(
        status=["TODO"],
        priority=["LOW"],
        assignee_id=42,
        page=1,
        limit=10,
        search="alpha",
    )

    assert base != task_list_query_hash(
        status=["DONE"],
        priority=["LOW"],
        assignee_id=42,
        page=1,
        limit=10,
        search="alpha",
    )
    assert base != task_list_query_hash(
        status=["TODO"],
        priority=["HIGH"],
        assignee_id=42,
        page=1,
        limit=10,
        search="alpha",
    )
    assert base != task_list_query_hash(
        status=["TODO"],
        priority=["LOW"],
        assignee_id=43,
        page=1,
        limit=10,
        search="alpha",
    )
    assert base != task_list_query_hash(
        status=["TODO"],
        priority=["LOW"],
        assignee_id=42,
        page=2,
        limit=10,
        search="alpha",
    )
    assert base != task_list_query_hash(
        status=["TODO"],
        priority=["LOW"],
        assignee_id=42,
        page=1,
        limit=20,
        search="alpha",
    )
    assert base != task_list_query_hash(
        status=["TODO"],
        priority=["LOW"],
        assignee_id=42,
        page=1,
        limit=10,
        search="beta",
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
            assert await real_redis.get(f"revoked_refresh_token:{jti}") == user_id

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
