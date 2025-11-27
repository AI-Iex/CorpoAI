import logging
from typing import Optional
from app.core.config import settings
from app.clients.interfaces.iam import IIAMClient
from app.clients.iam.iam_client import IAMClient

logger = logging.getLogger(__name__)

_iam_client: Optional[IIAMClient] = None


def init_iam_client() -> Optional[IIAMClient]:
    """
    Initialize IAM client if authentication is enabled.
    """
    global _iam_client

    if not settings.AUTH_ENABLED:
        logger.warning("IAM client initialization skipped (AUTH_ENABLED=False)")
        return None

    if _iam_client is not None:
        logger.warning("IAM client already initialized, returning existing instance")
        return _iam_client

    logger.debug(
        "Initializing IAM client",
        extra={
            "service_url": settings.IAM_SERVICE_URL,
            "api_version": settings.IAM_SERVICE_VERSION,
        },
    )

    _iam_client = IAMClient(
        base_url=settings.IAM_SERVICE_URL,
        service_version=settings.IAM_SERVICE_VERSION,
        client_id=settings.IAM_CLIENT_ID,
        client_secret=settings.IAM_CLIENT_SECRET,
        timeout=settings.IAM_SERVICE_TIMEOUT,
    )

    logger.debug("IAM client initialized successfully")
    return _iam_client


def get_iam_client() -> IIAMClient:
    """
    Get the IAM client singleton instance.
    """
    if not settings.AUTH_ENABLED:
        raise RuntimeError(
            "IAM client requested but AUTH_ENABLED is False, enable authentication in settings to use IAM service."
        )

    if _iam_client is None:
        raise RuntimeError("IAM client not initialized.")

    return _iam_client


def close_iam_client() -> None:
    """
    Close and cleanup IAM client resources.
    """
    global _iam_client

    if _iam_client is not None:
        logger.debug("Closing IAM client")
        _iam_client.close()
        _iam_client = None
        logger.debug("IAM client closed successfully")
    else:
        logger.warning("IAM client already closed or never initialized")
