"""Authentication business logic."""

import logging
from typing import Any

import jwt
from sqlalchemy.exc import IntegrityError

from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.core.constants import SECONDS_PER_DAY
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InactiveUser,
    InvalidCredentials,
    InvalidCurrentPassword,
    InvalidRefreshToken,
)
from app.core.redis import (
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    store_refresh_token,
)
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import ChangePasswordRequest

logger = logging.getLogger("taskhub.auth")


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    @staticmethod
    def _decode_refresh_token(token: str) -> dict[str, Any]:
        """Decode a refresh token and translate JWT errors."""
        try:
            return decode_refresh_token(token)
        except jwt.InvalidTokenError:
            raise InvalidRefreshToken() from None

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""

        existing_user = await self.user_repository.get_by_email(data.email)

        if existing_user is not None:
            raise EmailAlreadyRegistered()

        hashed_password = await hash_password(data.password)

        try:
            user = await self.user_repository.create(
                {
                    "email": data.email,
                    "full_name": data.full_name,
                    "hashed_password": hashed_password,
                }
            )
            await self.user_repository.session.commit()
            return user

        except IntegrityError:
            await self.user_repository.session.rollback()
            raise EmailAlreadyRegistered() from None

        except Exception:
            await self.user_repository.session.rollback()
            raise

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Change a user's password and revoke existing refresh sessions."""

        if not await verify_password(
            data.current_password,
            user.hashed_password,
        ):
            raise InvalidCurrentPassword()

        if data.current_password == data.new_password:
            raise InvalidCurrentPassword(
                "New password must be different from current password"
            )

        new_hashed_password = await hash_password(data.new_password)

        try:
            await self.user_repository.update(
                user.id,
                {"hashed_password": new_hashed_password},
            )
            await self.user_repository.session.commit()

        except Exception:
            await self.user_repository.session.rollback()
            raise

        try:
            await revoke_all_refresh_tokens(str(user.id))
        except Exception:
            logger.exception(
                "Failed to revoke refresh tokens after password change for user_id=%s",
                user.id,
            )

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and issue JWT tokens."""

        user = await self.user_repository.get_by_email(data.email)

        if user is None:
            await verify_password(data.password, DUMMY_PASSWORD_HASH)
            raise InvalidCredentials()

        password_valid = await verify_password(
            data.password,
            user.hashed_password,
        )

        if not password_valid:
            raise InvalidCredentials()

        if not user.is_active:
            raise InactiveUser()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        refresh_payload = self._decode_refresh_token(refresh_token)
        jti = refresh_payload["jti"]

        await store_refresh_token(
            jti=jti,
            user_id=str(user.id),
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * SECONDS_PER_DAY,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        """Rotate refresh token and issue new access token."""

        payload = self._decode_refresh_token(data.refresh_token)

        user_id = payload["sub"]
        old_jti = payload["jti"]

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise InvalidRefreshToken() from None

        user = await self.user_repository.get_by_id(user_id_int)

        if user is None:
            raise InvalidRefreshToken()

        if not user.is_active:
            raise InactiveUser()

        new_refresh_token = create_refresh_token(str(user.id))
        new_payload = self._decode_refresh_token(new_refresh_token)
        new_jti = new_payload["jti"]

        rotated = await rotate_refresh_token(
            old_jti=old_jti,
            new_jti=new_jti,
            user_id=str(user.id),
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * SECONDS_PER_DAY,
        )

        if not rotated:
            raise InvalidRefreshToken()

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=new_refresh_token,
        )

    async def logout(self, data: RefreshRequest) -> None:
        """Revoke a refresh token."""

        payload = self._decode_refresh_token(data.refresh_token)

        user_id = payload["sub"]
        jti = payload["jti"]

        try:
            int(user_id)
        except (ValueError, TypeError):
            raise InvalidRefreshToken() from None

        revoked = await revoke_refresh_token(
            jti=jti,
            user_id=user_id,
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * SECONDS_PER_DAY,
        )

        if not revoked:
            raise InvalidRefreshToken()
