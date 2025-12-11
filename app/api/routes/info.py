import logging
from fastapi import APIRouter, status
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/info", tags=["Info"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    summary="Get service info",
    description="**Get information about the service configuration.**",
)
async def info():
    """Get API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "log_level": settings.LOG_LEVEL,
        "auth_enabled": settings.AUTH_ENABLED,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
    }
