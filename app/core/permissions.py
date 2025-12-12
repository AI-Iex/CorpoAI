from fastapi import Depends, HTTPException, status
from typing import Optional
from app.schemas.token import TokenPayload
from app.schemas.user import User
from app.dependencies.auth import get_current_user
from app.core.config import settings


def requires_permission(permission_name: str) -> Optional[User]:
    """
    Dependency factory to check if the current user/client has the required permission.
    """

    async def checker(user_info: Optional[TokenPayload] = Depends(get_current_user)) -> Optional[User]:

        # If auth is disabled, return None
        if not settings.AUTH_ENABLED:
            return None

        # If auth is enabled but no user_info, error
        if user_info is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

        # 1. Check the type of the token
        if user_info.type == "user":
            print("User token detected")

        # 2. Check if user is not required to change password
        if user_info.require_password_change:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User must change password before proceeding"
            )

        # 3. Check if user has superuser status
        if user_info.is_superuser:
            return user_info

        # 4. Check if required permission is present
        if permission_name not in user_info.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return User(**user_info.model_dump())

    return checker
