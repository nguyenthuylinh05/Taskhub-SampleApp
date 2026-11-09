from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import InactiveUser, InvalidCredentials
from app.core.security import decode_token
from app.models import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Get the authenticated active user from an access token."""

    try:
        payload = decode_token(credentials.credentials)

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not isinstance(user_id, str) or token_type != "access":
            raise InvalidCredentials()

        user_id_int = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise InvalidCredentials() from None

    user_repository = UserRepository(session)
    user = await user_repository.get_by_id(user_id_int)

    if user is None:
        raise InvalidCredentials()

    if not user.is_active:
        raise InactiveUser()

    return user
