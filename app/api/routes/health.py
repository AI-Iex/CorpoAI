import logging
from typing import Optional
from fastapi import APIRouter, Depends, status
from app.dependencies.health import get_health_service
from app.schemas.health import HealthCheckResponse
from app.services.health.health_service import HealthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheckResponse,
    summary="Health check",
    description="**Check the health status of the service and its dependencies.**",
)
async def health_check(
    health_service: HealthService = Depends(get_health_service),
) -> HealthCheckResponse:
    """
    Return service health summary.
    """
    return await health_service.check_all()


from app.schemas.token import TokenPayload
from app.core.permissions import requires_permission
from app.core.permissions_loader import Permissions


@router.get(
    "/tokeninfo",
    status_code=status.HTTP_200_OK,
    response_model=Optional[TokenPayload],
    summary="Token check",
    description="**Check the token information.**",
)
async def token_info(
    user: Optional[TokenPayload] = Depends(requires_permission(Permissions.TOKEN_INFO)),
) -> Optional[TokenPayload]:
    """
    Return token information.
    Returns None if authentication is disabled.
    """
    return user
