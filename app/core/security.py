import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.schemas.token import TokenPayload

logger = logging.getLogger(__name__)

# Only create security scheme if auth is enabled (hides padlock in Swagger when disabled)
_http_bearer = HTTPBearer(auto_error=False) if settings.AUTH_ENABLED else None


async def _get_credentials() -> Optional[HTTPAuthorizationCredentials]:
    """Dummy dependency when auth is disabled."""
    return None


security = _http_bearer if settings.AUTH_ENABLED else _get_credentials


def decode_token(token: str) -> TokenPayload:
    """
    Decode and verify a JWT token.
    """
    try:
        payload_dict = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )

        payload = TokenPayload(**payload_dict)
        return payload

    except JWTError:
        raise UnauthorizedError("Invalid or expired token")
    except Exception:
        raise UnauthorizedError("Token validation failed")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """
    Get current authenticated user from JWT token.
    """
    # If authentication is disabled, no user
    if not settings.AUTH_ENABLED:
        logger.debug("Authentication disabled, no user validation")
        return None

    # Authentication is enabled, require credentials
    if not credentials:
        raise UnauthorizedError("Authentication required")

    try:
        token = credentials.credentials
        user_data = decode_token(token)
        logger.debug(f"User authenticated: {user_data.sub}")
        return user_data
    except Exception as e:
        raise UnauthorizedError(str(e))


async def require_permission(permission: str):
    """
    Dependency to require a specific permission.
    """

    async def _check_permission(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if current_user.is_superuser:
            return current_user

        if permission not in current_user.permissions:
            logger.debug(f"User {current_user.sub} lacks permission: {permission}")
            raise ForbiddenError("Not enough permissions")

        return current_user

    return _check_permission
