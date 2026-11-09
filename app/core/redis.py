from typing import cast

import redis.asyncio as redis

from app.core.config import REDIS_URL, REFRESH_TOKEN_EXPIRE_DAYS

redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def close_redis_connection() -> None:
    await redis_client.aclose()


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
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return cast(int, result)
