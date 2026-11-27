import hashlib
import json
import logging
from collections.abc import Iterable
from typing import cast

import redis.asyncio as redis

from app.core.config import REDIS_URL, REFRESH_TOKEN_EXPIRE_DAYS
from app.core.constants import SECONDS_PER_DAY

redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
)
logger = logging.getLogger("taskhub.cache")


def normalize_task_list_search(search: str | None) -> str | None:
    """Normalize search text for equivalent cache-key generation."""

    if search is None:
        return None
    normalized = search.strip().casefold()
    return normalized or None


def task_list_query_hash(
    status: Iterable[object] | None,
    priority: Iterable[object] | None,
    assignee_id: int | None,
    page: int,
    limit: int,
    search: str | None,
) -> str:
    """Build a canonical hash for task-list query parameters."""

    def normalized_values(values: Iterable[object] | None) -> list[str]:
        if values is None:
            return []
        return sorted({str(getattr(value, "value", value)) for value in values})

    canonical_query = {
        "status": normalized_values(status),
        "priority": normalized_values(priority),
        "assignee_id": assignee_id,
        "search": normalize_task_list_search(search),
        "page": page,
        "limit": limit,
    }
    return hashlib.sha256(
        json.dumps(
            canonical_query,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


async def close_redis_connection() -> None:
    await redis_client.aclose()


def task_list_cache_key(
    project_id: int,
    user_id: int,
    version: str,
    query_hash: str,
) -> str:
    """Build a versioned project/user task-list cache key."""

    return f"task-list:v1:{project_id}:{user_id}:{version}:{query_hash}"


async def get_task_list_cache_version(project_id: int) -> str | None:
    """Get or initialize a project task-list cache generation."""

    version_key = f"task-list:project:{project_id}:version"
    try:
        version = await redis_client.get(version_key)
        if version is None:
            created = await redis_client.set(version_key, "1", nx=True)
            if created:
                return "1"
            version = await redis_client.get(version_key)
        return str(version) if version is not None else "1"
    except Exception:
        logger.exception(
            "Redis task-list cache version read failed for project_id=%s",
            project_id,
        )
        return None


async def increment_task_list_cache_version(project_id: int) -> None:
    """Advance a project cache generation after a successful database commit."""

    version_key = f"task-list:project:{project_id}:version"
    try:
        await redis_client.incr(version_key)
    except Exception:
        logger.exception(
            "Redis task-list cache invalidation failed for project_id=%s",
            project_id,
        )


async def get_task_list_cached_response(cache_key: str) -> str | None:
    """Read a task-list JSON payload, returning None on Redis failure."""

    try:
        value = await redis_client.get(cache_key)
        return str(value) if value is not None else None
    except Exception:
        logger.exception("Redis task-list cache read failed for key=%s", cache_key)
        return None


async def set_task_list_cached_response(
    cache_key: str,
    payload: str,
    ttl_seconds: int,
) -> None:
    """Write a task-list JSON payload with TTL; Redis failures are non-fatal."""

    try:
        await redis_client.set(cache_key, payload, ex=ttl_seconds)
    except Exception:
        logger.exception("Redis task-list cache write failed for key=%s", cache_key)


async def store_refresh_token(
    jti: str,
    user_id: str,
    expire_seconds: int,
) -> None:
    """Store a refresh token and register its session."""

    pipeline = redis_client.pipeline(transaction=True)

    pipeline.set(
        f"refresh_token:{jti}",
        user_id,
        ex=expire_seconds,
    )
    pipeline.sadd(
        f"user_refresh_tokens:{user_id}",
        jti,
    )
    pipeline.expire(
        f"user_refresh_tokens:{user_id}",
        expire_seconds,
    )

    await pipeline.execute()


async def rotate_refresh_token(
    old_jti: str,
    new_jti: str,
    user_id: str,
    expire_seconds: int,
) -> bool:
    """Atomically rotate a refresh token.

    Returns:
        True: Rotation succeeded.
        False: Token is invalid or unknown.
        Reuse detection revokes all active refresh sessions.
    """

    script = """
    local old_key = KEYS[1]
    local new_key = KEYS[2]
    local user_sessions_key = KEYS[3]
    local revoked_key = KEYS[4]

    local expected_user_id = ARGV[1]
    local expire_seconds = tonumber(ARGV[2])

    local stored_user_id = redis.call("GET", old_key)

    -- Token is missing or no longer active.
    if stored_user_id ~= expected_user_id then

        -- A known revoked token is being reused.
        local revoked_user_id = redis.call("GET", revoked_key)

        if revoked_user_id == expected_user_id then

            local active_tokens = redis.call(
                "SMEMBERS",
                user_sessions_key
            )

            for _, jti in ipairs(active_tokens) do
                local token_key = "refresh_token:" .. jti
                local revoked_token_key = "revoked_refresh_token:" .. jti

                local stored_user_id = redis.call("GET", token_key)

                if stored_user_id == expected_user_id then
                    redis.call("DEL", token_key)
                redis.call(
                    "SET",
                    revoked_token_key,
                    expected_user_id,
                    "EX",
                    expire_seconds
                )
            end
        end

        redis.call("DEL", user_sessions_key)

            return -1
        end

        return 0
    end

    -- Revoke old token and remember its revocation.
    redis.call("DEL", old_key)

    redis.call(
        "SET",
        revoked_key,
        expected_user_id,
        "EX",
        expire_seconds
    )

    redis.call(
        "SREM",
        user_sessions_key,
        ARGV[3]
    )

    -- Store the new refresh token.
    redis.call(
        "SET",
        new_key,
        expected_user_id,
        "EX",
        expire_seconds
    )

    redis.call(
        "SADD",
        user_sessions_key,
        ARGV[4]
    )

    redis.call(
        "EXPIRE",
        user_sessions_key,
        expire_seconds
    )

    return 1
    """

    result = await redis_client.eval(
        script,
        4,
        f"refresh_token:{old_jti}",
        f"refresh_token:{new_jti}",
        f"user_refresh_tokens:{user_id}",
        f"revoked_refresh_token:{old_jti}",
        user_id,
        expire_seconds,
        old_jti,
        new_jti,
    )

    return cast(int, result) == 1


async def revoke_refresh_token(
    jti: str,
    user_id: str,
    expire_seconds: int,
) -> bool:
    """Atomically revoke one refresh token."""

    script = """
    local token_key = KEYS[1]
    local sessions_key = KEYS[2]
    local revoked_key = KEYS[3]

    local expected_user_id = ARGV[1]
    local expire_seconds = tonumber(ARGV[2])
    local jti = ARGV[3]

    local stored_user_id = redis.call("GET", token_key)

    if stored_user_id ~= expected_user_id then
        return 0
    end

    redis.call("DEL", token_key)

    redis.call(
        "SREM",
        sessions_key,
        jti
    )

    redis.call(
        "SET",
        revoked_key,
        expected_user_id,
        "EX",
        expire_seconds
    )

    return 1
    """

    result = await redis_client.eval(
        script,
        3,
        f"refresh_token:{jti}",
        f"user_refresh_tokens:{user_id}",
        f"revoked_refresh_token:{jti}",
        user_id,
        expire_seconds,
        jti,
    )

    return cast(int, result) == 1


async def revoke_all_refresh_tokens(user_id: str) -> int:
    """Revoke all active refresh tokens belonging to a user."""
    script = """
    local sessions_key = KEYS[1]
    local user_id = ARGV[1]
    local refresh_token_prefix = ARGV[2]
    local revoked_token_prefix = ARGV[3]
    local expire_seconds = tonumber(ARGV[4])

    local active_tokens = redis.call("SMEMBERS", sessions_key)
    local revoked_count = 0

    for _, jti in ipairs(active_tokens) do
        local token_key = refresh_token_prefix .. jti
        local stored_user_id = redis.call("GET", token_key)

        if stored_user_id == user_id then
            redis.call("DEL", token_key)
            redis.call(
                "SET",
                revoked_token_prefix .. jti,
                user_id,
                "EX",
                expire_seconds
            )
            revoked_count = revoked_count + 1
        end
    end

    redis.call("DEL", sessions_key)

    return revoked_count
    """

    result = await redis_client.eval(
        script,
        1,
        f"user_refresh_tokens:{user_id}",
        user_id,
        "refresh_token:",
        "revoked_refresh_token:",
        REFRESH_TOKEN_EXPIRE_DAYS * SECONDS_PER_DAY,
    )

    return cast(int, result)
