from typing import Optional
from fastapi import Depends
from app.core.security import get_current_user
from app.schemas.token import TokenPayload
from app.core.exceptions import UnauthorizedError, ForbiddenError


async def require_auth(
    current_user: Optional[TokenPayload] = Depends(get_current_user),
) -> TokenPayload:
    """
    Dependency that requires authentication.
    """
    if not current_user:
        raise UnauthorizedError("Authentication required for this endpoint")
    return current_user


async def require_superuser(
    current_user: Optional[TokenPayload] = Depends(require_auth),
) -> TokenPayload:
    """
    Dependency that requires the user to have superuser privileges.
    """
    if not current_user:
        raise UnauthorizedError("Authentication required for this endpoint")
    if current_user.is_superuser:
        return current_user
    else:
        raise ForbiddenError("Superuser privileges required")


async def get_user_id(
    current_user: Optional[TokenPayload] = Depends(get_current_user),
) -> Optional[str]:
    """
    Extract user ID from current user.
    """
    if not current_user:
        return None
    return current_user.sub
