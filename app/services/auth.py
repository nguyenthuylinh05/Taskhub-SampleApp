import jwt
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core import messages
from app.core.config import REFRESH_TOKEN_EXPIRE_SECONDS
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InactiveUser,
    InvalidCredentials,
    InvalidOperation,
    InvalidRefreshToken,
    NotFoundException,
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
    decode_token,
    hash_password,
    verify_password,
)
from app.models import TokenType, User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import ChangePasswordRequest


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""

        existing_user = await self.user_repository.get_by_email(str(data.email))

        if existing_user is not None:
            raise EmailAlreadyRegistered()

        hashed_password = await run_in_threadpool(
            hash_password,
            data.password,
        )

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

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Change user password and revoke all refresh tokens."""

        is_password_valid = await run_in_threadpool(
            verify_password,
            data.current_password,
            user.hashed_password,
        )

        if not is_password_valid:
            raise InvalidOperation(messages.CURRENT_PASSWORD_INCORRECT)

        if data.current_password == data.new_password:
            raise InvalidOperation(messages.NEW_PASSWORD_MUST_BE_DIFFERENT)

        await revoke_all_refresh_tokens(str(user.id))

        new_hashed_password = await run_in_threadpool(
            hash_password,
            data.new_password,
        )

        updated_user = await self.user_repository.update(
            user.id,
            {"hashed_password": new_hashed_password},
        )

        if updated_user is None:
            raise NotFoundException(messages.USER_NOT_FOUND)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and issue JWT tokens."""

        user = await self.user_repository.get_by_email(str(data.email))

        hashed_password = (
            user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
        )

        is_password_valid = await run_in_threadpool(
            verify_password,
            data.password,
            hashed_password,
        )

        if user is None or not is_password_valid:
            raise InvalidCredentials()

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        refresh_payload = decode_token(refresh_token)
        jti = refresh_payload.get("jti")

        if not isinstance(jti, str):
            raise InvalidRefreshToken()

        await store_refresh_token(
            jti=jti,
            user_id=str(user.id),
            expire_seconds=REFRESH_TOKEN_EXPIRE_SECONDS,
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
            or token_type != TokenType.REFRESH
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
            expire_seconds=REFRESH_TOKEN_EXPIRE_SECONDS,
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
            or token_type != TokenType.REFRESH
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
            expire_seconds=REFRESH_TOKEN_EXPIRE_SECONDS,
        )

        if not revoked:
            raise InvalidRefreshToken()
