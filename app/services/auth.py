import jwt
from sqlalchemy.exc import IntegrityError

from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InactiveUser,
    InvalidCredentials,
    InvalidRefreshToken,
)
from app.core.redis import (
    revoke_refresh_token,
    rotate_refresh_token,
    store_refresh_token,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
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


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""

        existing_user = await self.user_repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise EmailAlreadyRegistered()

        hashed_password = hash_password(data.password)

        try:
            return await self.user_repository.create(
                {
                    "email": str(data.email),
                    "full_name": data.full_name,
                    "hashed_password": hashed_password,
                }
            )
        except IntegrityError:
            await self.user_repository.session.rollback()
            raise EmailAlreadyRegistered() from None

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and issue JWT tokens."""

        user = await self.user_repository.get_by_email(str(data.email))

        if user is None or not verify_password(
            data.password,
            user.hashed_password,
        ):
            raise InvalidCredentials()

        if not user.is_active:
            raise InactiveUser()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        refresh_payload = decode_token(refresh_token)
        jti = refresh_payload.get("jti")

        if not isinstance(jti, str):
            raise InvalidRefreshToken()

        await store_refresh_token(
            jti=jti,
            user_id=str(user.id),
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        """Rotate refresh token and issue new access token."""

        try:
            payload = decode_token(data.refresh_token)
        except jwt.InvalidTokenError:
            raise InvalidRefreshToken() from None

        user_id = payload.get("sub")
        token_type = payload.get("type")
        old_jti = payload.get("jti")

        if (
            not isinstance(user_id, str)
            or token_type != "refresh"
            or not isinstance(old_jti, str)
        ):
            raise InvalidRefreshToken()

        try:
            user_id_int = int(user_id)
        except ValueError:
            raise InvalidRefreshToken() from None

        user = await self.user_repository.get_by_id(user_id_int)

        if user is None:
            raise InvalidRefreshToken()

        if not user.is_active:
            raise InactiveUser()

        new_refresh_token = create_refresh_token(str(user.id))
        new_payload = decode_token(new_refresh_token)
        new_jti = new_payload.get("jti")

        if not isinstance(new_jti, str):
            raise InvalidRefreshToken()

        rotated = await rotate_refresh_token(
            old_jti=old_jti,
            new_jti=new_jti,
            user_id=str(user.id),
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        if not rotated:
            raise InvalidRefreshToken()

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=new_refresh_token,
        )

    async def logout(self, data: RefreshRequest) -> None:
        """Revoke a refresh token."""

        try:
            payload = decode_token(data.refresh_token)
        except jwt.InvalidTokenError:
            raise InvalidRefreshToken() from None

        user_id = payload.get("sub")
        jti = payload.get("jti")
        token_type = payload.get("type")

        if (
            not isinstance(user_id, str)
            or token_type != "refresh"
            or not isinstance(jti, str)
        ):
            raise InvalidRefreshToken()

        try:
            int(user_id)
        except ValueError:
            raise InvalidRefreshToken() from None

        revoked = await revoke_refresh_token(
            jti=jti,
            user_id=user_id,
            expire_seconds=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

        if not revoked:
            raise InvalidRefreshToken()